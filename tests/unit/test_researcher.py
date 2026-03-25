"""Unit tests for Research agent."""

from unittest.mock import MagicMock, patch

import pytest

from src.agents.researcher import ResearchAgent, ResearchSectionResult
from src.state import SectionOutline, SearchResult as StateSearchResult
from src.tools.search import SearchResult as ToolSearchResult


class TestResearchAgent:
    """Tests for ResearchAgent."""

    @patch("src.agents.researcher.create_search_tool")
    def test_init(self, mock_create_search):
        """Test initialization."""
        agent = ResearchAgent()
        assert agent.search_tool is not None

    @patch("src.agents.researcher.create_search_tool")
    def test_research_section(self, mock_create_search):
        """Test single section research with LLM mocks."""
        mock_search = MagicMock()
        mock_search.search.return_value = [
            ToolSearchResult(
                title="Virat Kohli - Wikipedia",
                url="https://en.wikipedia.org/wiki/Virat_Kohli",
                snippet="Virat Kohli is an Indian cricketer who plays for India. He is known for his batting.",
                source="wikipedia",
                rank=0
            )
        ]
        mock_create_search.return_value = mock_search

        mock_llm = MagicMock()
        # Mock _generate_queries
        mock_llm.generate_json.return_value = ["Virat Kohli cricket"]
        # Mock _is_relevant
        mock_llm.generate_text.return_value = "YES"

        agent = ResearchAgent(llm_client=mock_llm, search_tool=mock_search)
        section = SectionOutline(title="Intro", research_goal="Goal")
        topic = "Virat Kohli"
        
        result = agent.research_section(topic, section)

        assert result.section_title == "Intro"
        assert len(result.search_results) == 1
        assert "Virat Kohli" in result.key_facts[0]
        assert "https://en.wikipedia.org/wiki/Virat_Kohli" in result.sources

    @patch("src.agents.researcher.create_search_tool")
    def test_to_state_results(self, mock_create_search):
        """Test conversion to state objects."""
        result = ResearchSectionResult(
            section_title="Test",
            search_results=[
                ToolSearchResult(title="T", url="U", snippet="C", source="wikipedia")
            ]
        )
        
        state_results = result.to_state_results()
        
        assert len(state_results) == 1
        assert isinstance(state_results[0], StateSearchResult)
        assert state_results[0].title == "T"
        assert state_results[0].content == "C"

    def test_build_search_query(self):
        """Test search query building (deprecated but still in code for now)."""
        agent = ResearchAgent(search_tool=MagicMock())
        section = SectionOutline(title="Early Life", research_goal="Family background")
        topic = "Virat Kohli"
        
        # This method might be removed later as per plan, but testing it if it exists
        if hasattr(agent, '_build_search_query'):
            query = agent._build_search_query(topic, section)
            assert query == "Virat Kohli Early Life"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
