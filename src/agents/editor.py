"""Editor agent for reviewing and improving sections."""

import logging
from typing import Any, Dict, List, Optional

from src.config import get_config
from src.llm.client import LLMClient
from src.prompts.editor_prompts import (
    CROSS_SECTION_REVIEW_PROMPT,
    EDITOR_REWRITE_PROMPT,
    EDITOR_REVIEW_PROMPT,
    EDITOR_SYSTEM_PROMPT,
)
from src.state import EditorFeedback, SectionDraft, SectionOutline, SearchResult

logger = logging.getLogger(__name__)

class EditorAgent:
    """Agent for reviewing and improving drafts."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.config = get_config()

    def review(self, topic: str, draft: SectionDraft, section: SectionOutline, research_data: List[SearchResult]) -> EditorFeedback:
        """Review a section draft."""
        context = self._build_research_context(research_data)
        prompt = EDITOR_REVIEW_PROMPT.format(
            topic=topic,
            section_title=section.title,
            target_words=section.estimated_word_count,
            word_count=draft.word_count,
            content=draft.content,
            research_context=context,
        )

        try:
            res = self.llm.generate_json(system_prompt=EDITOR_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.3)
            fb = EditorFeedback(
                issues=res.get("issues", []),
                suggestions=res.get("suggestions", []),
                needs_rewrite=res.get("needs_rewrite", False),
                severity=res.get("severity", "minor"),
            )
            return self._augment_feedback(fb, draft, section)
        except Exception as e:
            logger.error(f"Review failed: {e}")
            return self._automated_review(draft, section)

    def rewrite(self, topic: str, draft: SectionDraft, feedback: EditorFeedback, research_data: List[SearchResult]) -> str:
        """Rewrite section based on feedback."""
        context = self._build_research_context(research_data)
        prompt = EDITOR_REWRITE_PROMPT.format(
            topic=topic,
            section_title=draft.section_title,
            content=draft.content,
            feedback=self._format_feedback(feedback),
            research_context=context,
            word_count=draft.word_count,
        )
        try:
            return self.llm.generate_text(system_prompt=EDITOR_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.5)
        except Exception as e:
            logger.error(f"Rewrite failed: {e}")
            return draft.content

    def review_all_sections(self, topic: str, drafts: Dict[str, SectionDraft], sections: List[SectionOutline], research: Dict[str, List[SearchResult]], progress_callback: Optional[callable] = None) -> Dict[str, EditorFeedback]:
        """Review all sections."""
        fb_dict = {}
        for i, s in enumerate(sections):
            if drafts.get(s.title):
                fb_dict[s.title] = self.review(topic, drafts[s.title], s, research.get(s.title, []))
            if progress_callback: progress_callback(s.title, i + 1, len(sections))
        return fb_dict

    def cross_section_review(self, drafts: Dict[str, SectionDraft], sections: List[SectionOutline]) -> Dict[str, Any]:
        """Review for document-wide consistency."""
        full_content = [f"## {s.title}\n\n{drafts[s.title].content}" for s in sections if drafts.get(s.title)]
        prompt = CROSS_SECTION_REVIEW_PROMPT.format(
            section_titles="\n".join([f"- {s.title}" for s in sections]),
            full_content="\n\n".join(full_content),
        )
        try:
            res = self.llm.generate_json(system_prompt=EDITOR_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.3)
            return {
                "consistency_issues": res.get("consistency_issues", []),
                "flow_issues": res.get("flow_issues", []),
                "redundancies": res.get("redundancies", []),
                "recommendations": res.get("recommendations", []),
                "overall_quality": res.get("overall_quality", "unknown"),
            }
        except:
            return {"consistency_issues": [], "flow_issues": [], "redundancies": [], "recommendations": [], "overall_quality": "unknown"}

    def should_continue_revision(self, feedback: EditorFeedback, iteration_count: int) -> bool:
        """Check if more revisions are needed."""
        if iteration_count >= self.config.workflow.max_iterations: return False
        return feedback.needs_rewrite or feedback.severity == "major"

    def _build_research_context(self, data: List[SearchResult]) -> str:
        """Build research context string."""
        if not data: return "No data available."
        return "\n".join([f"{i}. **{r.title}** ({r.url})\n   {r.content[:300]}..." for i, r in enumerate(data[:5], 1)])

    def _format_feedback(self, fb: EditorFeedback) -> str:
        """Format feedback for prompt."""
        lines = ["### Issues"] + [f"- {i}" for i in fb.issues]
        lines += ["\n### Suggestions"] + [f"- {s}" for s in fb.suggestions]
        return "\n".join(lines)

    def _augment_feedback(self, fb: EditorFeedback, draft: SectionDraft, section: SectionOutline) -> EditorFeedback:
        """Add automated checks but don't force rewrite unless LLM said so."""
        issues, suggestions = list(fb.issues), list(fb.suggestions)
        target = section.estimated_word_count
        if draft.word_count < target * 0.7:
            issues.append(f"Content length: {draft.word_count}/{target}")
            suggestions.append("Consider adding more detail in next version")
        
        # Only rewrite if the LLM explicitly flagged it as major or needs_rewrite
        return EditorFeedback(
            issues=issues, 
            suggestions=suggestions, 
            needs_rewrite=fb.needs_rewrite, 
            severity=fb.severity
        )

    def _automated_review(self, draft: SectionDraft, section: SectionOutline) -> EditorFeedback:
        """Fallback review: Always approve to prevent getting stuck."""
        return EditorFeedback(
            issues=["Automated approval due to review timeout"], 
            suggestions=[], 
            needs_rewrite=False, 
            severity="minor"
        )
