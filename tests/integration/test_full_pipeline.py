"""Integration tests for the full research pipeline.

Tests the complete workflow with mocked LLM and search tools.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.graph import create_workflow
from src.state import create_initial_state


@pytest.fixture
def mock_llm_responses():
    """Mock responses for LLM calls throughout the pipeline."""
    return {
        "outline": {
            "sections": [
                {
                    "title": "Introduction to AI",
                    "research_goal": "Research AI basics, history, and current state",
                    "estimated_word_count": 400,
                    "order": 0,
                },
                {
                    "title": "Healthcare Applications",
                    "research_goal": "Find specific AI applications in healthcare with examples",
                    "estimated_word_count": 500,
                    "order": 1,
                },
                {
                    "title": "Future Implications",
                    "research_goal": "Research future trends and ethical considerations",
                    "estimated_word_count": 400,
                    "order": 2,
                },
            ]
        },
        "writer": "Artificial intelligence has emerged as a transformative force in modern healthcare. Studies demonstrate that AI systems achieve diagnostic accuracy rates exceeding 95% in specific domains [Source: https://example.com/study]. The technology continues to evolve rapidly, with new applications emerging across clinical workflows. Healthcare providers report significant efficiency gains, though challenges remain regarding integration and training.",
        "editor_review": {
            "issues": ["Minor flow improvement needed in paragraph 2"],
            "suggestions": ["Add transition sentence"],
            "needs_rewrite": False,
            "severity": "minor",
        },
        "summarizer": {
            "key_facts": ["AI achieves 95% accuracy in diagnosis", "Market growing 40% annually"],
            "main_points": ["Accuracy is high", "Adoption increasing"],
            "context": "Medical research context",
        },
    }


@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return [
        MagicMock(
            title="AI in Healthcare Study",
            url="https://example.com/study",
            snippet="AI achieves 95% accuracy",
        ),
        MagicMock(
            title="Healthcare AI Report",
            url="https://example.com/report",
            snippet="Market growing rapidly",
        ),
    ]


class TestFullPipeline:
    """Integration tests for complete pipeline."""

    @patch("src.nodes.PlannerAgent")
    @patch("src.nodes.ResearchAgent")
    @patch("src.nodes.WriterAgent")
    @patch("src.nodes.EditorAgent")
    @patch("src.nodes.DocumentCompiler")
    def test_complete_pipeline(
        self,
        mock_compiler,
        mock_editor,
        mock_writer,
        mock_researcher,
        mock_planner,
        mock_llm_responses,
    ):
        """Test complete pipeline execution."""
        from src.agents.planner import Outline
        from src.agents.researcher import ResearchSectionResult
        from src.state import SectionDraft, EditorFeedback

        # Setup planner mock
        from src.state import SectionOutline
        mock_planner_instance = MagicMock()
        mock_planner_instance.generate_outline.return_value = Outline(
            sections=[
                SectionOutline(
                    title="Introduction to AI",
                    research_goal="Research AI basics",
                    estimated_word_count=400,
                    order=0,
                ),
                SectionOutline(
                    title="Healthcare Applications",
                    research_goal="Find applications",
                    estimated_word_count=500,
                    order=1,
                ),
            ],
            topic="AI in Healthcare",
        )
        mock_planner.return_value = mock_planner_instance

        # Setup researcher mock
        mock_research_result = MagicMock(spec=ResearchSectionResult)
        mock_research_result.to_state_results.return_value = []
        mock_researcher_instance = MagicMock()
        mock_researcher_instance.research_section.return_value = mock_research_result
        mock_researcher.return_value = mock_researcher_instance

        # Setup writer mock
        mock_draft = SectionDraft(
            section_title="Test",
            content="This is generated content with proper citations [Source: https://example.com]. The section discusses AI applications extensively and meets the word count requirements.",
            sources_cited=["https://example.com"],
        )
        mock_writer_instance = MagicMock()
        mock_writer_instance.write_section.return_value = mock_draft
        mock_writer.return_value = mock_writer_instance

        # Setup editor mock
        mock_editor_instance = MagicMock()
        mock_editor_instance.review.return_value = EditorFeedback(
            needs_rewrite=False, severity="minor"
        )
        mock_editor_instance.should_continue_revision.return_value = False
        mock_editor.return_value = mock_editor_instance

        # Setup compiler mock
        mock_compiler_instance = MagicMock()
        mock_compiler_instance.compile.return_value = {
            "markdown": "output/ai-in-healthcare.md"
        }
        mock_compiler.return_value = mock_compiler_instance

        # Create and run workflow
        workflow = create_workflow(enable_human_review=False)

        initial_state = create_initial_state("AI in Healthcare")
        final_state = workflow.invoke(initial_state)

        # Assertions
        assert final_state["current_step"] == "completed"
        assert "final_document" in final_state
        assert final_state["final_document"]

    @patch("src.nodes.PlannerAgent")
    @patch("src.nodes.ResearchAgent")
    def test_pipeline_with_research_data(
        self,
        mock_researcher,
        mock_planner,
        mock_search_results,
    ):
        """Test pipeline with actual research data flow."""
        from src.agents.planner import Outline
        from src.state import SectionOutline

        # Setup planner
        mock_planner_instance = MagicMock()
        mock_planner_instance.generate_outline.return_value = Outline(
            sections=[
                SectionOutline(
                    title="Section 1",
                    research_goal="Goal 1",
                    estimated_word_count=400,
                    order=0,
                ),
            ],
            topic="Test",
        )
        mock_planner.return_value = mock_planner_instance

        # Setup researcher with results
        from src.agents.researcher import ResearchSectionResult
        from src.tools import SearchResult as ToolSearchResult
        from src.tools.scraper import ScrapedContent
        from src.tools.summarizer import Summary

        mock_research_result = MagicMock(spec=ResearchSectionResult)
        mock_research_result.section_title = "Section 1"
        mock_research_result.to_state_results.return_value = [
            MagicMock(
                title="Test Source",
                url="https://example.com",
                content="Test content",
                source="test",
            )
        ]
        mock_researcher_instance = MagicMock()
        mock_researcher_instance.research_section.return_value = mock_research_result
        mock_researcher.return_value = mock_researcher_instance

        # Run workflow
        workflow = create_workflow(enable_human_review=False)
        state = create_initial_state("Test Topic")
        state["outline"] = [
            {"title": "Section 1", "research_goal": "Goal", "estimated_word_count": 400, "order": 0}
        ]

        # Just test planning and research nodes
        from src.nodes import planning_node, research_node

        planned = planning_node(state)
        assert "outline" in planned

        researched = research_node(planned)
        assert "research" in researched


class TestPipelineEdgeCases:
    """Tests for edge cases in the pipeline."""

    @patch("src.nodes.PlannerAgent")
    def test_pipeline_error_handling(self, mock_planner):
        """Test error handling in pipeline."""
        mock_planner.side_effect = Exception("LLM unavailable")

        from src.nodes import planning_node

        state = create_initial_state("Test")
        result = planning_node(state)

        assert result["current_step"] == "error"
        assert len(result["errors"]) > 0

    @patch("src.nodes.WriterAgent")
    def test_pipeline_empty_research(self, mock_writer):
        """Test writing with empty research data."""
        from src.state import SectionDraft

        mock_writer_instance = MagicMock()
        mock_writer_instance.write_section.return_value = SectionDraft(
            section_title="Test",
            content="Content based on general knowledge.",
        )
        mock_writer.return_value = mock_writer_instance

        from src.nodes import writing_node

        state = create_initial_state("Test")
        state["outline"] = [
            {"title": "Section", "research_goal": "Goal", "estimated_word_count": 400, "order": 0}
        ]
        state["research"] = {"Section": []}  # Empty research

        result = writing_node(state)

        assert "drafts" in result
        mock_writer_instance.write_section.assert_called_once()


class TestPipelinePerformance:
    """Tests for pipeline performance characteristics."""

    def test_state_size_management(self):
        """Test that state doesn't grow excessively."""
        state = create_initial_state("Test Topic")

        # Add typical data
        state["outline"] = [
            {"title": f"Section {i}", "research_goal": f"Goal {i}", "estimated_word_count": 400, "order": i}
            for i in range(6)
        ]

        state["drafts"] = {
            f"Section {i}": {
                "section_title": f"Section {i}",
                "content": "Content " * 200,  # ~400 words
                "word_count": 400,
                "sources_cited": ["source1", "source2"],
            }
            for i in range(6)
        }

        # Check state is reasonable size
        import json
        state_json = json.dumps(state)
        assert len(state_json) < 100000  # Should be under 100KB

    def test_checkpoint_compatibility(self):
        """Test that state is serializable for checkpoints."""
        import json

        state = create_initial_state("Test")
        state["outline"] = [
            {"title": "Test", "research_goal": "Goal", "estimated_word_count": 400, "order": 0}
        ]

        # Should be JSON serializable
        serialized = json.dumps(state)
        deserialized = json.loads(serialized)

        assert deserialized["topic"] == state["topic"]
        assert len(deserialized["outline"]) == 1


class TestPipelineOutputQuality:
    """Tests for output quality metrics."""

    def test_document_completeness(self):
        """Test that generated document is complete."""
        # This would check:
        # - All sections present
        # - Proper citations
        # - Word count targets met
        # - No placeholder text
        pass  # Would require full LLM integration

    def test_citation_integrity(self):
        """Test that citations are properly formatted."""
        # Check for [Source: ...] pattern
        # Verify all citations have corresponding sources
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
