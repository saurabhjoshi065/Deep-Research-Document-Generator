"""Planner agent for document outlines."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.config import get_config
from src.llm.client import LLMClient
from src.prompts.planner_prompts import (
    OUTLINE_FORMAT_INSTRUCTIONS,
    PLANNER_SYSTEM_PROMPT,
)
from src.state import SectionOutline

logger = logging.getLogger(__name__)

@dataclass
class Outline:
    """Document outline."""
    topic: str
    sections: List[SectionOutline] = field(default_factory=list)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> Dict[str, Any]:
        return {"topic": self.topic, "sections": [s.to_dict() for s in self.sections]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Outline":
        return cls(topic=data.get("topic", ""), sections=[SectionOutline.from_dict(s) for s in data.get("sections", [])])

class PlannerAgent:
    """Agent for generating document outlines."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.config = get_config()

    def generate_outline(self, topic: str, expected_sections: Optional[int] = None) -> Outline:
        """Generate outline for a topic."""
        expected_sections = expected_sections or self.config.workflow.sections_count
        prompt = f"Topic: {topic}\nSections: {expected_sections}\n{OUTLINE_FORMAT_INSTRUCTIONS}"
        
        response = self.llm.generate_json(system_prompt=PLANNER_SYSTEM_PROMPT, user_prompt=prompt)
        outline = self._parse_outline(response, topic)
        self._validate_outline(outline, expected_sections)
        return outline

    def _parse_outline(self, response: Dict[str, Any], topic: str) -> Outline:
        """Parse LLM response to Outline."""
        sections = [SectionOutline(title=s.get("title", ""), research_goal=s.get("research_goal", ""), estimated_word_count=s.get("estimated_word_count", 450)) for s in response.get("sections", [])]
        return Outline(topic=topic, sections=sections)

    def _validate_outline(self, outline: Outline, expected_sections: int):
        """Validate outline structure."""
        if not outline.sections: raise ValueError("Outline has no sections")
        if len(outline.sections) < 2: raise ValueError(f"Expected >= 2 sections, got {len(outline.sections)}")
        for s in outline.sections:
            if not s.title: raise ValueError("Section missing title")
            if not s.research_goal: raise ValueError(f"Section '{s.title}' missing research goal")

    def refine_outline(self, outline: Outline, feedback: str) -> Outline:
        """Refine outline based on feedback."""
        prompt = f"Outline: {outline.to_dict()}\nFeedback: {feedback}\n{OUTLINE_FORMAT_INSTRUCTIONS}"
        response = self.llm.generate_json(system_prompt=PLANNER_SYSTEM_PROMPT, user_prompt=prompt)
        return self._parse_outline(response, outline.topic)

    def preview_outline(self, outline: Outline) -> str:
        """Get readable outline string."""
        return "\n".join([f"{i}. {s.title} (~{s.estimated_word_count} words)\n   Goal: {s.research_goal}" for i, s in enumerate(outline.sections, 1)])
