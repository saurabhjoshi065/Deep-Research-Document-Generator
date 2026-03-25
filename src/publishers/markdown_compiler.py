"""Markdown compiler for generating Markdown documents.

Creates well-formatted Markdown with table of contents and metadata.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.state import SectionDraft


class MarkdownCompiler:
    """Compiler for Markdown output format."""

    def __init__(self, include_toc: bool = True, include_metadata: bool = True):
        """Initialize Markdown compiler.

        Args:
            include_toc: Whether to include table of contents
            include_metadata: Whether to include metadata header
        """
        self.include_toc = include_toc
        self.include_metadata = include_metadata

    def compile(
        self,
        sections: List[SectionDraft],
        title: str,
        output_path: Optional[Path] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Compile sections into Markdown document.

        Args:
            sections: Section drafts
            title: Document title
            output_path: Optional path to save file
            metadata: Optional metadata dictionary

        Returns:
            Markdown content as string
        """
        lines = []

        # Add metadata header
        if self.include_metadata:
            lines.extend(self._generate_metadata(title, metadata))
            lines.append("")

        # Add title
        lines.append(f"# {title}")
        lines.append("")

        # Add table of contents
        if self.include_toc:
            lines.extend(self._generate_toc(sections))
            lines.append("")

        # Add sections
        for draft in sections:
            lines.extend(self._format_section(draft))
            lines.append("")

        # Add sources section
        lines.extend(self._generate_sources(sections))

        markdown = "\n".join(lines)

        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.write_text(markdown, encoding="utf-8")

        return markdown

    def _generate_metadata(
        self,
        title: str,
        metadata: Optional[Dict] = None,
    ) -> List[str]:
        """Generate metadata header in YAML format.

        Args:
            title: Document title
            metadata: Additional metadata

        Returns:
            Metadata lines
        """
        lines = ["---"]
        # lines.append(f'title: "{title}"') # Remove title from YAML if redundant
        lines.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
        lines.append(f"generated_by: Deep Research Document Generator")

        if metadata:
            for key, value in metadata.items():
                if key == "title": continue # Skip if title is passed in metadata dict
                if isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")

        lines.append("---")
        return lines

    def _generate_toc(self, sections: List[SectionDraft]) -> List[str]:
        """Generate table of contents.

        Args:
            sections: Section drafts

        Returns:
            TOC lines
        """
        lines = ["## Table of Contents", ""]

        for i, draft in enumerate(sections, 1):
            anchor = self._generate_anchor(draft.section_title)
            lines.append(f"{i}. [{draft.section_title}](#{anchor})")

        return lines

    def _format_section(self, draft: SectionDraft) -> List[str]:
        """Format a single section.

        Args:
            draft: Section draft

        Returns:
            Formatted section lines
        """
        lines = []

        # Section header
        anchor = self._generate_anchor(draft.section_title)
        lines.append(f"<a id='{anchor}'></a>")
        lines.append(f"## {draft.section_title}")
        lines.append("")

        # Section content
        content = draft.content.strip()
        lines.append(content)

        return lines

    def _generate_sources(self, sections: List[SectionDraft]) -> List[str]:
        """Generate sources/citations section.

        Args:
            sections: Section drafts

        Returns:
            Sources section lines
        """
        # Collect all unique sources
        all_sources = set()
        for draft in sections:
            all_sources.update(draft.sources_cited)

        if not all_sources:
            return []

        lines = ["---", "", "## Sources", ""]

        for i, source in enumerate(sorted(all_sources), 1):
            lines.append(f"{i}. {source}")

        return lines

    def _generate_anchor(self, title: str) -> str:
        """Generate anchor link from title.

        Args:
            title: Section title

        Returns:
            Anchor string
        """
        # Convert to lowercase, replace spaces with hyphens
        anchor = title.lower().replace(" ", "-")
        # Remove non-alphanumeric characters except hyphens
        anchor = "".join(c for c in anchor if c.isalnum() or c == "-")
        # Remove consecutive hyphens
        while "--" in anchor:
            anchor = anchor.replace("--", "-")
        return anchor.strip("-")


def compile_document(
    sections: List[SectionDraft],
    title: str,
    output_path: Path,
    format: str = "markdown",
    **kwargs,
) -> Path:
    """Compile document in specified format.

    Args:
        sections: Section drafts
        title: Document title
        output_path: Output file path
        format: Output format (only markdown supported)
        **kwargs: Additional compiler options

    Returns:
        Path to generated file
    """
    if format == "markdown":
        compiler = MarkdownCompiler(**kwargs)
        compiler.compile(sections, title, output_path)
        return output_path

    else:
        raise ValueError(f"Unsupported format: {format}. Only 'markdown' is currently supported.")
