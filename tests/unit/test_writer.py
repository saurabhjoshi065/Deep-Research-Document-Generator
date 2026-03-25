"""Unit tests for Writer agent."""

import re
from unittest.mock import MagicMock, patch

import pytest

from src.agents.writer import WriterAgent
from src.state import SectionDraft, SectionOutline, SearchResult


class TestWriterAgentInit:
    """Tests for WriterAgent initialization."""

    def test_init_default(self):
        """Test initialization with defaults."""
        agent = WriterAgent()

        assert agent.llm is not None
        assert agent.config is not None


class TestWriterAgentWriting:
    """Tests for WriterAgent writing functionality."""

    @patch("src.agents.writer.LLMClient")
    def test_write_section(self, mock_llm_class):
        """Test basic section writing."""
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "This is the section content [Source: http://example.com]."
        mock_llm_class.return_value = mock_llm

        agent = WriterAgent(llm_client=mock_llm)

        section = SectionOutline(
            title="Introduction",
            research_goal="Research AI basics",
            estimated_word_count=400,
        )

        research = [
            SearchResult(
                title="AI Basics",
                url="http://example.com",
                content="AI is broad.",
                source="test",
            )
        ]
        topic = "AI"

        draft = agent.write_section(topic, section, research)

        assert draft.section_title == "Introduction"
        assert "section content" in draft.content
        assert "http://example.com" in draft.sources_cited
        assert draft.word_count > 0

    @patch("src.agents.writer.LLMClient")
    def test_write_all_sections(self, mock_llm_class):
        """Test writing multiple sections."""
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "Content"
        mock_llm_class.return_value = mock_llm

        agent = WriterAgent(llm_client=mock_llm)

        sections = [
            SectionOutline(title="S1", research_goal="G1"),
            SectionOutline(title="S2", research_goal="G2"),
        ]

        research = {"S1": [], "S2": []}
        topic = "Topic"

        drafts = agent.write_all_sections(topic, sections, research)

        assert len(drafts) == 2
        assert "S1" in drafts
        assert "S2" in drafts


class TestWriterAgentRevision:
    """Tests for WriterAgent revision functionality."""

    @patch("src.agents.writer.LLMClient")
    def test_revise_section(self, mock_llm_class):
        """Test section revision based on feedback."""
        mock_llm = MagicMock()
        mock_llm.generate_text.return_value = "Revised content [Source: http://new.com]."
        mock_llm_class.return_value = mock_llm

        agent = WriterAgent(llm_client=mock_llm)

        draft = SectionDraft(
            section_title="Test",
            content="Original content",
            sources_cited=["http://old.com"],
        )

        feedback = "Add more detail about trends."
        research = []
        topic = "Topic"

        revised = agent.revise_section(topic, draft, feedback, research)

        assert "Revised content" in revised.content
        assert "http://new.com" in revised.sources_cited
        assert revised.revision_count == 1


class TestWriterAgentUtilities:
    """Tests for WriterAgent utility methods."""

    def test_build_research_context(self):
        """Test research context string building."""
        agent = WriterAgent()

        research = [
            SearchResult(title="T1", url="http://1.com", content="C1", source="s"),
            SearchResult(title="T2", url="http://2.com", content="C2", source="s"),
        ]

        context = agent._build_research_context(research)

        assert "Source 1: T1" in context
        assert "Source 2: T2" in context
        assert "http://1.com" in context

    def test_post_process(self):
        """Test content cleaning."""
        agent = WriterAgent()

        raw = "Certainly! Here is the content:\n\nMain content here."
        cleaned = agent._post_process(raw)

        assert cleaned == "Main content here."

    def test_extract_citations(self):
        """Test citation extraction from text."""
        agent = WriterAgent()

        content = "Claims [Source: http://a.com] and [Source: http://b.com]"
        sources = agent._extract_citations(content)

        assert "http://a.com" in sources
        assert "http://b.com" in sources
        assert len(sources) == 2

    def test_count_citations(self):
        """Test citation counting."""
        agent = WriterAgent()

        content = "[Source: A] and [Source: B] and [Source: A]"
        count = agent.count_citations(content)

        assert count == 3

    def test_estimate_quality(self):
        """Test quality estimation."""
        agent = WriterAgent()

        draft = SectionDraft(
            section_title="Test",
            content="This has ten words here for testing purposes now truly.",
            sources_cited=["Source 1", "Source 2"],
        )

        metrics = agent.estimate_quality(draft)

        assert metrics["word_count"] == 10
        assert metrics["citation_count"] == 0
        assert metrics["sources_cited_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
