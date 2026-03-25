"""Writer agent for drafting sections."""

import re
from typing import Dict, List, Optional

from src.config import get_config
from src.llm.client import LLMClient
from src.prompts.writer_prompts import (
    CITATION_INSTRUCTIONS,
    SECTION_WRITING_PROMPT,
    WRITER_SYSTEM_PROMPT,
)
from src.state import SectionDraft, SectionOutline, SearchResult

class WriterAgent:
    """Agent for drafting document sections."""

    DEFAULT_WORD_COUNT = 450

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.config = get_config()

    def write_section(self, topic: str, section: SectionOutline, research_data: List[SearchResult], target_words: Optional[int] = None) -> SectionDraft:
        """Write a single section."""
        target_words = target_words or section.estimated_word_count
        context = self._build_research_context(research_data)
        prompt = SECTION_WRITING_PROMPT.format(
            topic=topic,
            section_title=section.title,
            target_words=target_words,
            word_count=0,
            research_data=context,
        ) + CITATION_INSTRUCTIONS

        content = self.llm.generate_text(
            system_prompt=WRITER_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.7,
            max_tokens=int(target_words * 1.5),
        )

        content = self._post_process(content)
        sources = self._extract_citations(content)

        return SectionDraft(section_title=section.title, content=content, sources_cited=sources)

    def write_all_sections(self, topic: str, sections: List[SectionOutline], research: Dict[str, List[SearchResult]], progress_callback: Optional[callable] = None) -> Dict[str, SectionDraft]:
        """Write all sections."""
        drafts = {}
        for i, section in enumerate(sections):
            if progress_callback: progress_callback(section.title, i + 1, len(sections))
            drafts[section.title] = self.write_section(topic, section, research.get(section.title, []))
        return drafts

    def revise_section(self, topic: str, draft: SectionDraft, feedback: str, research_data: List[SearchResult]) -> SectionDraft:
        """Revise a section based on feedback."""
        context = self._build_research_context(research_data)
        prompt = f"Topic: {topic}\n\nRevise based on feedback.\n\nOriginal: {draft.content}\n\nFeedback: {feedback}\n\nData: {context}" + CITATION_INSTRUCTIONS

        content = self.llm.generate_text(system_prompt=WRITER_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.5)
        content = self._post_process(content)
        sources = self._extract_citations(content)

        return SectionDraft(
            section_title=draft.section_title,
            content=content,
            sources_cited=sources,
            revision_count=draft.revision_count + 1,
        )

    def _build_research_context(self, research_data: List[SearchResult]) -> str:
        """Build context string."""
        if not research_data: return "No specific research data."
        return "\n".join([f"Source {i}: {r.title} ({r.url})\nContent: {r.content[:500]}..." for i, r in enumerate(research_data, 1)])

    def _post_process(self, content: str) -> str:
        """Clean meta-commentary."""
        content = content.strip()
        patterns = [r"^Here is the section content:.*", r"^Certainly!.*", r"^Section Content:.*"]
        for pattern in patterns:
            content = re.sub(pattern, "", content, flags=re.IGNORECASE).strip()
        return content

    def _extract_citations(self, content: str) -> List[str]:
        """Extract [Source: URL] citations."""
        matches = re.findall(r"\[Source:\s*(.*?)\]", content)
        return list(set(s.strip() for s in matches))

    def count_citations(self, content: str) -> int:
        """Count citation occurrences."""
        return len(re.findall(r"\[Source:", content))

    def estimate_quality(self, draft: SectionDraft) -> Dict[str, any]:
        """Get quality metrics."""
        word_count = len(draft.content.split())
        citation_count = self.count_citations(draft.content)
        return {
            "word_count": word_count,
            "target_word_count": self.DEFAULT_WORD_COUNT,
            "citation_count": citation_count,
            "sources_cited_count": len(draft.sources_cited),
            "revision_count": draft.revision_count,
            "meets_word_target": word_count >= self.DEFAULT_WORD_COUNT * 0.8,
            "has_citations": citation_count >= 2,
        }
