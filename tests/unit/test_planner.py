"""Unit tests for Planner agent."""

from unittest.mock import MagicMock, patch
import pytest
from src.agents.planner import PlannerAgent, Outline
from src.state import SectionOutline

class TestOutline:
    def test_create_outline(self):
        sections = [SectionOutline(title="S1", research_goal="G1")]
        outline = Outline(topic="Test", sections=sections)
        assert outline.topic == "Test"
        assert outline.section_count == 1

    def test_to_dict(self):
        sections = [SectionOutline(title="S1", research_goal="G1")]
        outline = Outline(topic="Test", sections=sections)
        data = outline.to_dict()
        assert data["topic"] == "Test"
        assert len(data["sections"]) == 1

class TestPlannerAgent:
    @patch("src.llm.client.LLMClient")
    def test_generate_outline_success(self, mock_llm):
        mock_llm.generate_json.return_value = {
            "sections": [
                {"title": "Intro", "research_goal": "G1", "estimated_word_count": 400},
                {"title": "Body", "research_goal": "G2", "estimated_word_count": 500}
            ]
        }
        agent = PlannerAgent(llm_client=mock_llm)
        outline = agent.generate_outline("Test Topic")
        assert outline.section_count == 2
        assert outline.sections[0].title == "Intro"

    def test_validate_outline_error(self):
        agent = PlannerAgent()
        outline = Outline(topic="Test", sections=[])
        with pytest.raises(ValueError, match="Outline has no sections"):
            agent._validate_outline(outline, 5)

    def test_preview_outline(self):
        agent = PlannerAgent()
        sections = [SectionOutline(title="Intro", research_goal="G1")]
        outline = Outline(topic="Test", sections=sections)
        preview = agent.preview_outline(outline)
        assert "Intro" in preview
