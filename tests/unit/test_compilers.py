"""Unit tests for compilers."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.publishers import DocumentCompiler
from src.publishers.markdown_compiler import MarkdownCompiler
from src.state import SectionDraft


class TestMarkdownCompiler:
    """Tests for MarkdownCompiler."""

    def test_compile_basic(self, tmp_path):
        """Test basic Markdown compilation."""
        compiler = MarkdownCompiler()

        sections = [
            SectionDraft(section_title="Section 1", content="Content 1"),
            SectionDraft(section_title="Section 2", content="Content 2"),
        ]

        output_path = tmp_path / "test.md"
        result = compiler.compile(sections, "Test Document", output_path)

        assert output_path.exists()
        assert "# Test Document" in result
        assert "## Section 1" in result
        assert "## Section 2" in result
        assert "Content 1" in result

    def test_compile_with_metadata(self, tmp_path):
        """Test compilation with metadata."""
        compiler = MarkdownCompiler(include_metadata=True)

        sections = [
            SectionDraft(section_title="Section 1", content="Content"),
        ]

        metadata = {"author": "Test Author", "tags": ["test", "research"]}
        output_path = tmp_path / "test.md"
        result = compiler.compile(sections, "Test", output_path, metadata)

        assert "---" in result  # YAML front matter
        assert "author: Test Author" in result
        assert "- test" in result

    def test_compile_with_toc(self, tmp_path):
        """Test compilation with table of contents."""
        compiler = MarkdownCompiler(include_toc=True)

        sections = [
            SectionDraft(section_title="Introduction", content="Intro content"),
            SectionDraft(section_title="Conclusion", content="Conclusion content"),
        ]

        output_path = tmp_path / "test.md"
        result = compiler.compile(sections, "Test", output_path)

        assert "## Table of Contents" in result
        assert "[Introduction]" in result
        assert "[Conclusion]" in result

    def test_compile_with_sources(self, tmp_path):
        """Test compilation with sources section."""
        compiler = MarkdownCompiler()

        sections = [
            SectionDraft(
                section_title="Section",
                content="Content [Source: http://example.com]",
                sources_cited=["http://example.com"],
            ),
        ]

        output_path = tmp_path / "test.md"
        result = compiler.compile(sections, "Test", output_path)

        assert "## Sources" in result
        assert "http://example.com" in result

    def test_generate_anchor(self):
        """Test anchor generation."""
        compiler = MarkdownCompiler()

        assert compiler._generate_anchor("Section Title") == "section-title"
        assert compiler._generate_anchor("Title With -- Hyphens") == "title-with-hyphens"
        assert compiler._generate_anchor("UPPER CASE") == "upper-case"


class TestDocumentCompiler:
    """Tests for DocumentCompiler."""

    @patch("src.publishers.DocumentCompiler._compile_markdown")
    def test_compile_markdown(self, mock_compile_md, tmp_path):
        """Test Markdown compilation via unified interface."""
        mock_compile_md.return_value = tmp_path / "test.md"

        from src.config import OutputConfig
        config = OutputConfig(output_dir=tmp_path, formats=["markdown"])

        compiler = DocumentCompiler(config)
        sections = [SectionDraft(section_title="S1", content="C1")]

        results = compiler.compile(sections, "Test Document", formats=["markdown"])

        assert "markdown" in results
        mock_compile_md.assert_called_once()

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from src.config import OutputConfig
        compiler = DocumentCompiler(OutputConfig())

        assert compiler._sanitize_filename("Test Document") == "test-document"
        assert compiler._sanitize_filename("Special!@#Chars") == "specialchars"
        assert compiler._sanitize_filename("A" * 100) == "a" * 50  # Truncated

    def test_get_document_stats(self):
        """Test document statistics."""
        from src.config import OutputConfig
        compiler = DocumentCompiler(OutputConfig())

        sections = [
            SectionDraft(section_title="S1", content="One two three", sources_cited=["A"]),
            SectionDraft(section_title="S2", content="Four five", sources_cited=["A", "B"]),
        ]

        stats = compiler.get_document_stats(sections)

        assert stats["section_count"] == 2
        assert stats["total_words"] == 5
        assert stats["total_citations"] == 3
        assert stats["total_sources"] == 2  # Unique sources
        assert stats["average_section_length"] == 2.5

    def test_unsupported_format(self, tmp_path):
        """Test error on unsupported format."""
        from src.config import OutputConfig
        compiler = DocumentCompiler(OutputConfig())

        # PDF is now unsupported
        with pytest.raises(ValueError, match="Unsupported format: pdf"):
            compiler.compile([], "Test", formats=["pdf"])


class TestCompilerIntegration:
    """Integration tests for compilers."""

    def test_full_markdown_pipeline(self, tmp_path):
        """Test complete Markdown compilation pipeline."""
        from src.config import OutputConfig

        config = OutputConfig(
            output_dir=tmp_path,
            formats=["markdown"],
            include_toc=True,
            include_metadata=True,
        )

        compiler = DocumentCompiler(config)

        sections = [
            SectionDraft(
                section_title="Introduction",
                content="This is the introduction. It provides context.",
                sources_cited=["http://example.com/intro"],
            ),
            SectionDraft(
                section_title="Main Content",
                content="This is the main content with citations [Source: http://example.com/main].",
                sources_cited=["http://example.com/main"],
            ),
        ]

        metadata = {
            "topic": "Test Topic",
            "generated_by": "Test",
        }

        results = compiler.compile(sections, "Test Report", metadata=metadata)

        assert "markdown" in results

        # Verify content
        content = results["markdown"].read_text(encoding="utf-8")
        assert "# Test Report" in content
        assert "## Introduction" in content
        assert "## Main Content" in content
        assert "## Table of Contents" in content
        assert "## Sources" in content
        # Note: topic: Test Topic is now in the YAML metadata
        assert "topic: Test Topic" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
