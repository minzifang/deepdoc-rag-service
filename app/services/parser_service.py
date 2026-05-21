import logging
from pathlib import Path
from timeit import default_timer as timer
from typing import Any, Callable

from app.core.config import get_settings
from app.core.vendor import bootstrap_ragflow_vendor
from app.models.schemas import ParserMode

ProgressCallback = Callable[[float, str], None]


class DeepDocPdfAdapter:
    """Small standalone adapter over RAGFlowPdfParser.

    The methods it calls are official DeepDoc internals; the service wrapper
    adds page limits, task callbacks, fallback, and explicit parser metadata.
    """

    def __init__(self) -> None:
        bootstrap_ragflow_vendor()
        from deepdoc.parser.pdf_parser import RAGFlowPdfParser

        self._parser = RAGFlowPdfParser()

    def parse(self, path: Path, from_page: int, to_page: int, callback: ProgressCallback) -> tuple[list[Any], list[Any]]:
        start = timer()
        zoomin = 3

        callback(0.12, "DeepDoc OCR started")
        self._parser.outlines = []
        self._parser.__images__(str(path), zoomin, from_page, to_page, lambda p=None, msg="": callback(0.12 + (p or 0) * 0.45, msg))
        callback(0.56, f"DeepDoc OCR finished ({timer() - start:.2f}s)")

        start = timer()
        self._parser._layouts_rec(zoomin)
        callback(0.66, f"Layout analysis finished ({timer() - start:.2f}s)")

        start = timer()
        self._parser._table_transformer_job(zoomin)
        callback(0.72, f"Table analysis finished ({timer() - start:.2f}s)")

        start = timer()
        self._parser._text_merge(zoomin=zoomin)
        callback(0.76, f"Text merge finished ({timer() - start:.2f}s)")

        tables = self._parser._extract_table_figure(True, zoomin, True, True)
        self._parser._naive_vertical_merge()
        self._parser._concat_downward()
        sections = [(box["text"], self._parser._line_tag(box, zoomin)) for box in self._parser.boxes]
        callback(0.8, "DeepDoc parsing finished")
        return sections, tables


class ParserService:
    def parse(
        self,
        path: Path,
        filename: str,
        mode: ParserMode,
        from_page: int,
        to_page: int | None,
        callback: ProgressCallback,
    ) -> tuple[str, list[Any], list[Any]]:
        suffix = path.suffix.lower()
        settings = get_settings()
        effective_to_page = min(to_page or settings.max_page_number, settings.max_page_number)

        if suffix == ".pdf":
            return self._parse_pdf(path, mode, from_page, effective_to_page, callback)
        if suffix == ".docx":
            return self._parse_docx(path, callback)
        if suffix in {".txt", ".md", ".markdown", ".py", ".js", ".ts", ".java", ".go", ".sql", ".csv"}:
            return self._parse_text(path, callback)

        raise ValueError(f"unsupported file type: {suffix or filename}")

    def _parse_pdf(
        self,
        path: Path,
        mode: ParserMode,
        from_page: int,
        to_page: int,
        callback: ProgressCallback,
    ) -> tuple[str, list[Any], list[Any]]:
        if mode in {"auto", "deepdoc"}:
            try:
                sections, tables = DeepDocPdfAdapter().parse(path, from_page, to_page, callback)
                return "deepdoc", sections, tables
            except Exception as exc:
                if mode == "deepdoc":
                    raise
                logging.exception("DeepDoc failed, falling back to plain PDF parser: %s", exc)
                callback(0.2, f"DeepDoc unavailable, fallback to plain parser: {exc}")

        return self._parse_plain_pdf(path, from_page, to_page, callback)

    def _parse_plain_pdf(
        self,
        path: Path,
        from_page: int,
        to_page: int,
        callback: ProgressCallback,
    ) -> tuple[str, list[Any], list[Any]]:
        callback(0.2, "Plain PDF text extraction started")
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        sections = []
        for page in reader.pages[from_page:to_page]:
            text = page.extract_text() or ""
            sections.extend((line.strip(), "") for line in text.splitlines() if line.strip())
        tables = []
        callback(0.8, "Plain PDF text extraction finished")
        return "plain", sections, tables

    def _parse_docx(self, path: Path, callback: ProgressCallback) -> tuple[str, list[Any], list[Any]]:
        bootstrap_ragflow_vendor()
        from deepdoc.parser import DocxParser

        callback(0.2, "DOCX parsing started")
        sections, tables = DocxParser()(str(path))
        callback(0.8, "DOCX parsing finished")
        return "deepdoc-docx", sections, tables

    def _parse_text(self, path: Path, callback: ProgressCallback) -> tuple[str, list[Any], list[Any]]:
        callback(0.2, "Text parsing started")
        text = path.read_text(encoding="utf-8", errors="ignore")
        sections = [(part.strip(), "") for part in text.splitlines() if part.strip()]
        callback(0.8, "Text parsing finished")
        return "plain-text", sections, []
