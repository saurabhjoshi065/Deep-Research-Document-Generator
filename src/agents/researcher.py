"""Research agent using Wikipedia."""

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from src.config import get_config
from src.llm.client import LLMClient
from src.state import SearchResult as StateSearchResult, SectionOutline
from src.tools import (
    SearchResult as ToolSearchResult,
    create_search_tool,
)

logger = logging.getLogger(__name__)

@dataclass
class ResearchSectionResult:
    """Results for a single section."""
    section_title: str
    search_results: List[ToolSearchResult] = field(default_factory=list)
    key_facts: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    def to_state_results(self) -> List[StateSearchResult]:
        """Convert to state storage format."""
        return [
            StateSearchResult(
                title=res.title,
                url=res.url,
                content=res.snippet,
                source="wikipedia",
            ) for res in self.search_results
        ]

class ResearchAgent:
    """Agent for Wikipedia-based research."""

    def __init__(self, llm_client: Optional[LLMClient] = None, search_tool=None):
        self.config = get_config()
        self.llm = llm_client or LLMClient()
        self.search_tool = search_tool or create_search_tool()

    def research_section(self, topic: str, section: SectionOutline, num_results: int = 2, progress_callback: Optional[Callable] = None) -> ResearchSectionResult:
        """Research a single section with LLM-based refinement and filtering."""
        logger.info(f"Researching: {section.title}")
        if progress_callback: progress_callback("searching", 0, 1)

        # 1. Generate optimized search queries
        queries = self._generate_queries(topic, section)
        
        all_results = []
        seen_urls = set()
        
        for query in queries:
            search_results = self._search(query, num_results)
            for res in search_results:
                if res.url not in seen_urls:
                    all_results.append(res)
                    seen_urls.add(res.url)

        # 2. Filter results for relevance using LLM
        relevant_results = []
        for res in all_results:
            if self._is_relevant(topic, section, res):
                relevant_results.append(res)
        
        # If no relevant results found, fallback to original list but log warning
        if not relevant_results and all_results:
            logger.warning(f"No results passed LLM relevance filter for {section.title}. Using all results.")
            relevant_results = all_results

        # Extract facts from summaries
        key_facts = []
        for res in relevant_results:
            sentences = [s.strip() for s in res.snippet.split('.') if len(s.strip()) > 20]
            key_facts.extend(sentences[:5])

        sources = list(set([r.url for r in relevant_results if r.url]))
        if progress_callback: progress_callback("complete", 1, 1)

        return ResearchSectionResult(
            section_title=section.title,
            search_results=relevant_results,
            key_facts=key_facts[:15],
            sources=sources,
        )

    def _generate_queries(self, topic: str, section: SectionOutline) -> List[str]:
        """Use LLM to generate 2-3 specific search queries."""
        prompt = f"""Generate 3 specific Wikipedia search queries for a research section.
Topic: {topic}
Section Title: {section.title}
Research Goal: {section.research_goal}

Requirements:
- Queries should be short (3-6 words)
- Focused on specific facts and keywords
- Avoid broad or poetic language
- Each query must include the main topic name: {topic}

Return as a simple JSON list: ["query1", "query2", "query3"]"""
        
        try:
            queries = self.llm.generate_json(system_prompt="You are a research assistant.", user_prompt=prompt)
            if isinstance(queries, list) and queries:
                return queries[:3]
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
        
        # Fallback
        return [f"{topic} {section.title}"]

    def _is_relevant(self, topic: str, section: SectionOutline, result: ToolSearchResult) -> bool:
        """Use LLM to check if a search result is relevant to the topic and section."""
        prompt = f"""EVALUATE SEARCH RESULT RELEVANCE

We are writing a research paper about: **{topic}**
The current section is: **{section.title}**

Is the following Wikipedia search result relevant and useful for this paper?

---
RESULT TITLE: {result.title}
RESULT SUMMARY: {result.snippet[:800]}
---

RELEVANCE CRITERIA:
1. **Direct Match**: If the result is the main Wikipedia page for **{topic}**, it is ALWAYS relevant (YES).
2. **Topical Match**: If the result discusses people, events, or concepts directly connected to **{topic}** in a meaningful way, it is relevant (YES).
3. **Irrelevant**: If the result is about a completely different person, a different sport, a fictional character with the same name, or an unrelated concept that only happens to share a keyword, it is NOT relevant (NO).

Does this result provide accurate information for a paper about **{topic}**?
Respond with exactly "YES" or "NO"."""
        
        try:
            response = self.llm.generate_text(system_prompt="You are a senior research reviewer. Your goal is to ensure only highly relevant data is used for the paper.", user_prompt=prompt, temperature=0.1).strip().upper()
            is_relevant = "YES" in response
            if not is_relevant:
                logger.info(f"Filtered out irrelevant result: {result.title}")
            return is_relevant
        except Exception as e:
            logger.error(f"Relevance check failed: {e}")
            return True # Default to true on error


    def research_all_sections(self, topic: str, sections: List[SectionOutline], progress_callback: Optional[Callable] = None) -> Dict[str, ResearchSectionResult]:
        """Research all sections."""
        results = {}
        for i, section in enumerate(sections):
            if progress_callback: progress_callback(section.title, i + 1, len(sections))
            results[section.title] = self.research_section(topic, section)
        return results

    def _build_search_query(self, topic: str, section: SectionOutline) -> str:
        """Build search query from section."""
        return f"{topic} {section.title}"

    def _search(self, query: str, num_results: int) -> List[ToolSearchResult]:
        """Execute search."""
        try:
            results = self.search_tool.search(query, num_results)
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_research_summary(self, result: ResearchSectionResult) -> str:
        """Generate formatted summary."""
        lines = [f"## Summary: {result.section_title}", f"\n**Sources**: {len(result.sources)}", "\n### Key Findings"]
        for i, fact in enumerate(result.key_facts[:10], 1):
            lines.append(f"{i}. {fact}")
        lines.append("\n### Sources")
        for source in result.sources[:5]:
            lines.append(f"- {source}")
        return "\n".join(lines)
