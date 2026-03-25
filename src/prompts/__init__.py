"""Prompt templates for agent interactions."""

from src.prompts.planner_prompts import PLANNER_SYSTEM_PROMPT, OUTLINE_FORMAT_INSTRUCTIONS
from src.prompts.writer_prompts import WRITER_SYSTEM_PROMPT
from src.prompts.editor_prompts import EDITOR_SYSTEM_PROMPT, EDITOR_REVIEW_PROMPT, EDITOR_REWRITE_PROMPT

__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "OUTLINE_FORMAT_INSTRUCTIONS",
    "WRITER_SYSTEM_PROMPT",
    "EDITOR_SYSTEM_PROMPT",
    "EDITOR_REVIEW_PROMPT",
    "EDITOR_REWRITE_PROMPT",
]
