"""Unit tests for state schema."""

import pytest
from datetime import datetime

from src.state import (
    SectionOutline,
    SearchResult,
    SectionDraft,
    EditorFeedback,
    create_initial_state,
    update_state,
    add_error,
    get_total_word_count,
    get_research_stats,
)


class TestSectionOutline:
    """Tests for SectionOutline dataclass."""

    def test_create_section_outline(self):
        """Test creating a basic section outline."""
        outline = SectionOutline(
            title="Introduction",
            research_goal="Provide overview of AI in healthcare",
            estimated_word_count=500,
            order=0,
        )

        assert outline.title == "Introduction"
        assert outline.research_goal == "Provide overview of AI in healthcare"
        assert outline.estimated_word_count == 500
        assert outline.order == 0

    def test_default_values(self):
        """Test default values are set correctly."""
        outline = SectionOutline(title="Test", research_goal="Test goal")

        assert outline.estimated_word_count == 450
        assert outline.order == 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        outline = SectionOutline(
            title="Methods",
            research_goal="Describe methodology",
            estimated_word_count=400,
            order=1,
        )
        data = outline.to_dict()

        assert data["title"] == "Methods"
        assert data["research_goal"] == "Describe methodology"
        assert data["estimated_word_count"] == 400
        assert data["order"] == 1

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "title": "Results",
            "research_goal": "Present findings",
            "estimated_word_count": 600,
            "order": 2,
        }
        outline = SectionOutline.from_dict(data)

        assert outline.title == "Results"
        assert outline.estimated_word_count == 600

    def test_round_trip(self):
        """Test dict -> from_dict round trip preserves data."""
        original = SectionOutline(
            title="Conclusion",
            research_goal="Summarize key points",
            estimated_word_count=300,
            order=3,
        )
        restored = SectionOutline.from_dict(original.to_dict())

        assert original.title == restored.title
        assert original.research_goal == restored.research_goal
        assert original.estimated_word_count == restored.estimated_word_count
        assert original.order == restored.order


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_create_search_result(self):
        """Test creating a search result."""
        result = SearchResult(
            title="AI in Healthcare Report",
            url="https://example.com/report",
            content="Healthcare AI is growing rapidly...",
            source="DuckDuckGo",
            relevance_score=0.85,
        )

        assert result.title == "AI in Healthcare Report"
        assert result.url == "https://example.com/report"
        assert result.source == "DuckDuckGo"
        assert result.relevance_score == 0.85
        assert isinstance(result.timestamp, datetime)

    def test_default_timestamp(self):
        """Test timestamp defaults to now."""
        before = datetime.now()
        result = SearchResult(
            title="Test",
            url="http://test.com",
            content="Content",
            source="Test",
        )
        after = datetime.now()

        assert before <= result.timestamp <= after

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = SearchResult(
            title="Test",
            url="http://test.com",
            content="Content",
            source="Test",
        )
        data = result.to_dict()

        assert data["title"] == "Test"
        assert data["url"] == "http://test.com"
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "title": "Test",
            "url": "http://test.com",
            "content": "Content",
            "source": "Test",
            "timestamp": "2024-01-15T10:30:00",
            "relevance_score": 0.9,
        }
        result = SearchResult.from_dict(data)

        assert result.title == "Test"
        assert result.timestamp == datetime(2024, 1, 15, 10, 30, 0)


class TestSectionDraft:
    """Tests for SectionDraft dataclass."""

    def test_create_section_draft(self):
        """Test creating a section draft."""
        draft = SectionDraft(
            section_title="Introduction",
            content="This is the introduction. It has multiple sentences.",
            sources_cited=["Source 1", "Source 2"],
        )

        assert draft.section_title == "Introduction"
        assert draft.word_count == 8  # Auto-calculated
        assert len(draft.sources_cited) == 2

    def test_word_count_calculation(self):
        """Test word count is calculated correctly."""
        draft = SectionDraft(
            section_title="Test",
            content="One two three four five.",
        )

        assert draft.word_count == 5

    def test_empty_content(self):
        """Test handling of empty content."""
        draft = SectionDraft(section_title="Empty", content="")

        assert draft.word_count == 0

    def test_to_dict(self):
        """Test serialization."""
        draft = SectionDraft(
            section_title="Methods",
            content="Methodology description here.",
            sources_cited=["Ref 1"],
            revision_count=2,
        )
        data = draft.to_dict()

        assert data["section_title"] == "Methods"
        assert data["word_count"] == 3
        assert data["revision_count"] == 2


class TestEditorFeedback:
    """Tests for EditorFeedback dataclass."""

    def test_create_feedback(self):
        """Test creating editor feedback."""
        feedback = EditorFeedback(
            issues=["Tone inconsistency", "Weak opening"],
            suggestions=["Use more formal language", "Add hook"],
            needs_rewrite=True,
            severity="moderate",
        )

        assert len(feedback.issues) == 2
        assert feedback.needs_rewrite is True
        assert feedback.severity == "moderate"

    def test_default_values(self):
        """Test default values."""
        feedback = EditorFeedback()

        assert feedback.issues == []
        assert feedback.needs_rewrite is False
        assert feedback.severity == "minor"

    def test_round_trip(self):
        """Test dict serialization round trip."""
        original = EditorFeedback(
            issues=["Issue 1"],
            suggestions=["Fix 1"],
            needs_rewrite=True,
            severity="major",
        )
        restored = EditorFeedback.from_dict(original.to_dict())

        assert original.issues == restored.issues
        assert original.needs_rewrite == restored.needs_rewrite


class TestStateFunctions:
    """Tests for state utility functions."""

    def test_create_initial_state(self):
        """Test initial state creation."""
        state = create_initial_state("AI in Healthcare")

        assert state["topic"] == "AI in Healthcare"
        assert state["current_step"] == "planning"
        assert state["errors"] == []
        assert state["outline"] == []
        assert state["research"] == {}
        assert state["drafts"] == {}
        assert state["final_document"] == ""
        assert state["user_approved"] is False
        assert state["max_iterations"] == 3

    def test_update_state(self):
        """Test state update function."""
        state = create_initial_state("Test")
        updated = update_state(state, current_step="researching", iteration_count=1)

        assert updated["current_step"] == "researching"
        assert updated["iteration_count"] == 1
        assert updated["topic"] == "Test"  # Original preserved
        # Original state unchanged
        assert state["current_step"] == "planning"

    def test_add_error(self):
        """Test error addition."""
        state = create_initial_state("Test")
        updated = add_error(state, "Connection failed")

        assert len(updated["errors"]) == 1
        assert updated["errors"][0] == "Connection failed"
        assert updated["current_step"] == "error"

    def test_add_multiple_errors(self):
        """Test adding multiple errors."""
        state = create_initial_state("Test")
        state = add_error(state, "Error 1")
        state = add_error(state, "Error 2")

        assert len(state["errors"]) == 2

    def test_get_total_word_count(self):
        """Test total word count calculation."""
        state = create_initial_state("Test")
        state["drafts"] = {
            "Section 1": SectionDraft(section_title="Section 1", content="One two three"),
            "Section 2": SectionDraft(section_title="Section 2", content="Four five six seven"),
        }

        assert get_total_word_count(state) == 7

    def test_get_total_word_count_empty(self):
        """Test word count with no drafts."""
        state = create_initial_state("Test")

        assert get_total_word_count(state) == 0

    def test_get_research_stats(self):
        """Test research statistics."""
        state = create_initial_state("Test")
        state["research"] = {
            "Section 1": [
                SearchResult("R1", "http://1.com", "C1", "DDG"),
                SearchResult("R2", "http://2.com", "C2", "DDG"),
            ],
            "Section 2": [
                SearchResult("R3", "http://3.com", "C3", "DDG"),
            ],
            "Section 3": [],  # Empty section
        }
        stats = get_research_stats(state)

        assert stats["total_sections"] == 3
        assert stats["sections_with_research"] == 2
        assert stats["total_results"] == 3
        assert stats["average_per_section"] == 1.0

    def test_get_research_stats_empty(self):
        """Test research stats with no research."""
        state = create_initial_state("Test")
        stats = get_research_stats(state)

        assert stats["total_sections"] == 0
        assert stats["average_per_section"] == 0


class TestStateWorkflowTransitions:
    """Tests for state transitions through workflow."""

    def test_planning_to_researching(self):
        """Test transition from planning to researching."""
        state = create_initial_state("Test")

        # Create outline
        outline = [
            SectionOutline(title="Intro", research_goal="Overview"),
            SectionOutline(title="Body", research_goal="Details"),
        ]
        state = update_state(state, outline=outline, current_step="researching")

        assert state["current_step"] == "researching"
        assert len(state["outline"]) == 2

    def test_researching_to_writing(self):
        """Test transition from researching to writing."""
        state = create_initial_state("Test")
        state["current_step"] = "researching"

        # Add research results
        research = {
            "Intro": [SearchResult("R1", "http://1.com", "Content", "DDG")],
        }
        state = update_state(state, research=research, current_step="writing")

        assert state["current_step"] == "writing"
        assert "Intro" in state["research"]

    def test_writing_to_editing(self):
        """Test transition from writing to editing."""
        state = create_initial_state("Test")
        state["current_step"] = "writing"

        # Add drafts
        drafts = {
            "Intro": SectionDraft(section_title="Intro", content="Introduction text here."),
        }
        state = update_state(state, drafts=drafts, current_step="editing")

        assert state["current_step"] == "editing"
        assert state["drafts"]["Intro"].word_count == 3

    def test_editing_to_compiling(self):
        """Test transition from editing to compiling."""
        state = create_initial_state("Test")
        state["current_step"] = "editing"
        state["iteration_count"] = 1

        state = update_state(state, current_step="compiling")

        assert state["current_step"] == "compiling"

    def test_editor_feedback_loop(self):
        """Test editor feedback loop increments counter."""
        state = create_initial_state("Test")
        state["current_step"] = "editing"

        # Simulate rewrite needed
        feedback = EditorFeedback(needs_rewrite=True, severity="major")
        state = update_state(
            state,
            current_feedback=feedback,
            section_being_revised="Intro",
            current_step="writing",  # Back to writing
            iteration_count=state["iteration_count"] + 1,
        )

        assert state["current_step"] == "writing"
        assert state["iteration_count"] == 1
        assert state["section_being_revised"] == "Intro"

    def test_complete_workflow(self):
        """Test complete workflow state transitions."""
        state = create_initial_state("AI in Healthcare")

        # Planning
        state["outline"] = [
            SectionOutline("Introduction", "Overview of AI in healthcare"),
            SectionOutline("Applications", "Current AI applications"),
        ]
        state["user_approved"] = True
        state["current_step"] = "researching"

        # Researching
        state["research"] = {
            "Introduction": [SearchResult("R1", "http://1.com", "Content", "DDG")],
            "Applications": [SearchResult("R2", "http://2.com", "Content", "DDG")],
        }
        state["current_step"] = "writing"

        # Writing
        state["drafts"] = {
            "Introduction": SectionDraft("Introduction", "Intro text here."),
            "Applications": SectionDraft("Applications", "Applications text here."),
        }
        state["current_step"] = "editing"

        # Editing (no rewrites needed)
        state["current_step"] = "compiling"

        # Compiling
        state["final_document"] = "# AI in Healthcare\n\nFull document..."
        state["current_step"] = "completed"

        assert state["current_step"] == "completed"
        assert len(state["drafts"]) == 2
        assert state["final_document"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
