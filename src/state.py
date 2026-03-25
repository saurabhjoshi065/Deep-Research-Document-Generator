"""Shared state schema for the research document generator.

This module defines the TypedDict state classes used throughout the LangGraph
workflow. These schemas ensure type safety and provide a clear contract between
nodes.
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SectionOutline:
    """Represents a planned section in the document outline.

    Attributes:
        title: The section title
        research_goal: What information needs to be gathered for this section
        estimated_word_count: Target word count for this section (default: 450)
        order: Position in the document (0-indexed)
    """

    title: str
    research_goal: str
    estimated_word_count: int = 450
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "research_goal": self.research_goal,
            "estimated_word_count": self.estimated_word_count,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionOutline":
        """Create from dictionary."""
        return cls(
            title=data["title"],
            research_goal=data["research_goal"],
            estimated_word_count=data.get("estimated_word_count", 450),
            order=data.get("order", 0),
        )


@dataclass
class SearchResult:
    """Represents a single web search result.

    Attributes:
        title: The result title
        url: Source URL
        content: Extracted/summarized content
        source: Search engine or tool name
        timestamp: When the result was fetched
        relevance_score: Optional relevance score (0-1)
    """

    title: str
    url: str
    content: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    relevance_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "relevance_score": self.relevance_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        return cls(
            title=data["title"],
            url=data["url"],
            content=data["content"],
            source=data["source"],
            timestamp=timestamp or datetime.now(),
            relevance_score=data.get("relevance_score"),
        )


@dataclass
class SectionDraft:
    """Represents a drafted section of the document.

    Attributes:
        section_title: The section title
        content: The written content
        word_count: Actual word count
        sources_cited: List of sources cited in this section
        revision_count: Number of revisions made
    """

    section_title: str
    content: str
    word_count: int = 0
    sources_cited: List[str] = field(default_factory=list)
    revision_count: int = 0

    def __post_init__(self) -> None:
        """Calculate word count if not provided."""
        if self.word_count == 0 and self.content:
            self.word_count = len(self.content.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "section_title": self.section_title,
            "content": self.content,
            "word_count": self.word_count,
            "sources_cited": self.sources_cited,
            "revision_count": self.revision_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectionDraft":
        """Create from dictionary."""
        return cls(
            section_title=data["section_title"],
            content=data["content"],
            word_count=data.get("word_count", 0),
            sources_cited=data.get("sources_cited", []),
            revision_count=data.get("revision_count", 0),
        )


@dataclass
class EditorFeedback:
    """Represents feedback from the editor agent.

    Attributes:
        issues: List of identified issues
        suggestions: Specific improvement suggestions
        needs_rewrite: Whether the section needs to be rewritten
        severity: Overall severity assessment
    """

    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    needs_rewrite: bool = False
    severity: Literal["minor", "moderate", "major"] = "minor"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "issues": self.issues,
            "suggestions": self.suggestions,
            "needs_rewrite": self.needs_rewrite,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EditorFeedback":
        """Create from dictionary."""
        return cls(
            issues=data.get("issues", []),
            suggestions=data.get("suggestions", []),
            needs_rewrite=data.get("needs_rewrite", False),
            severity=data.get("severity", "minor"),
        )


class ResearchState(TypedDict, total=False):
    """Shared state for the LangGraph research workflow.

    This TypedDict defines the complete state that flows through the graph.
    All fields are optional (total=False) to allow partial state updates.

    Required Fields:
        topic: The original user query/topic

    Workflow Fields:
        current_step: Current node being executed
        errors: List of error messages encountered
        iteration_count: Number of editor feedback loops completed

    Content Fields:
        outline: Planned document structure
        research: Raw research data keyed by section title
        drafts: Written section drafts keyed by section title
        final_document: Compiled final output

    Control Fields:
        user_approved: Whether user has approved the outline
        max_iterations: Maximum editor revision loops (default: 3)
        output_format: Desired output format ("markdown" or "pdf")
    """

    # Required
    topic: str

    # Workflow tracking
    current_step: Literal[
        "planning",
        "researching",
        "writing",
        "editing",
        "compiling",
        "completed",
        "error",
    ]
    errors: List[str]
    iteration_count: int

    # Content
    outline: List[SectionOutline]
    research: Dict[str, List[SearchResult]]
    drafts: Dict[str, SectionDraft]
    final_document: str

    # Control
    user_approved: bool
    max_iterations: int
    output_format: Literal["markdown", "pdf", "both"]

    # Editor feedback
    current_feedback: Optional[EditorFeedback]
    section_being_revised: Optional[str]


def create_initial_state(topic: str) -> Dict[str, Any]:
    """Factory function to create initial state.

    Args:
        topic: The research topic

    Returns:
        Initial state dictionary
    """
    return {
        "topic": topic,
        "current_step": "planning",
        "errors": [],
        "iteration_count": 0,
        "outline": [],
        "research": {},
        "drafts": {},
        "final_document": "",
        "user_approved": False,
        "max_iterations": 3,
        "output_format": "markdown",
        "current_feedback": None,
        "section_being_revised": None,
    }


def update_state(state: Dict[str, Any], **updates: Any) -> Dict[str, Any]:
    """Update state with new values.

    Args:
        state: Current state
        **updates: Key-value pairs to update

    Returns:
        Updated state (new dictionary)
    """
    new_state = state.copy()
    new_state.update(updates)
    return new_state


def add_error(state: Dict[str, Any], error_message: str) -> Dict[str, Any]:
    """Add an error message to state and set step to 'error'.

    Args:
        state: Current state
        error_message: Error description

    Returns:
        Updated state
    """
    errors = list(state.get("errors", []))
    errors.append(error_message)
    return update_state(state, errors=errors, current_step="error")


def get_total_word_count(state: Dict[str, Any]) -> int:
    """Calculate total word count from all drafts.

    Args:
        state: Current state

    Returns:
        Total word count
    """
    drafts = state.get("drafts", {})
    total = 0
    for draft in drafts.values():
        if isinstance(draft, dict):
            total += draft.get("word_count", 0)
        else:
            total += getattr(draft, "word_count", 0)
    return total


def get_research_stats(state: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics about research data.

    Args:
        state: Current state

    Returns:
        Dictionary with research statistics
    """
    research = state.get("research", {})
    total_results = sum(len(results) for results in research.values())
    sections_with_research = sum(1 for results in research.values() if results)

    return {
        "total_sections": len(research),
        "sections_with_research": sections_with_research,
        "total_results": total_results,
        "average_per_section": total_results / len(research) if research else 0,
    }
