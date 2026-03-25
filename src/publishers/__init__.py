"""Unified compiler interface for document generation."""

from pathlib import Path
from typing import Dict, List, Optional

from src.config import OutputConfig, get_config
from src.publishers.markdown_compiler import MarkdownCompiler
from src.publishers.docx_compiler import DocxCompiler
from src.state import SectionDraft

class DocumentCompiler:
    """Unified document compiler supporting Markdown and Word."""

    SUPPORTED_FORMATS = ["markdown", "md", "docx"]

    def __init__(self, config: Optional[OutputConfig] = None):
        self.config = config or get_config().output
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def compile(self, sections: List[SectionDraft], title: str, formats: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> Dict[str, Path]:
        """Compile document in specified format(s)."""
        formats = formats or ["markdown", "docx"]
        metadata = metadata or {}
        results = {}

        for fmt in formats:
            f = fmt.lower()
            if f in ["markdown", "md"]:
                results["markdown"] = self._compile_markdown(sections, title, metadata)
            elif f == "docx":
                results["docx"] = self._compile_docx(sections, title, metadata)
        return results

    def _compile_markdown(self, sections: List[SectionDraft], title: str, metadata: Dict) -> Path:
        safe_title = self._sanitize_filename(title)
        path = self.config.output_dir / f"{safe_title}.md"
        MarkdownCompiler(include_toc=self.config.include_toc, include_metadata=self.config.include_metadata).compile(sections, title, path, metadata)
        return path

    def _compile_docx(self, sections: List[SectionDraft], title: str, metadata: Dict) -> Path:
        safe_title = self._sanitize_filename(title)
        path = self.config.output_dir / f"{safe_title}.docx"
        DocxCompiler().compile(sections, title, path, metadata)
        return path

    def _sanitize_filename(self, title: str) -> str:
        safe = title.replace(" ", "-").replace("_", "-")
        safe = "".join(c for c in safe if c.isalnum() or c in "-_")
        if len(safe) > 50: safe = safe[:50]
        return safe.rstrip("-").lower() or "document"

    def get_document_stats(self, sections: List[SectionDraft]) -> Dict:
        """Get document statistics."""
        def get_val(obj, attr, default=None):
            return obj.get(attr, default) if isinstance(obj, dict) else getattr(obj, attr, default)

        total_words = sum(get_val(d, "word_count", 0) for d in sections)
        sources = set(src for d in sections for src in get_val(d, "sources_cited", []))
        
        return {
            "section_count": len(sections),
            "total_words": total_words,
            "total_sources": len(sources),
            "sections": [{"title": get_val(d, "section_title"), "words": get_val(d, "word_count", 0)} for d in sections],
        }
