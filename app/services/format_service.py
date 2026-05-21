import re
import statistics
from html.parser import HTMLParser
from typing import Any


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            self._current_row.append(" ".join("".join(self._current_cell).split()))
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            if any(cell for cell in self._current_row):
                self.rows.append(self._current_row)
            self._current_row = None


class FormatService:
    """Render parser output into text/markdown.

    DeepDoc gives us a list of sections. Each section can be:
      - a 2-tuple/list ``(text, position_tag)`` from the older pipeline,
        where ``position_tag`` looks like ``"@@page\\tx0\\tx1\\ttop\\tbottom##"``
        and we have no semantic layout label;
      - a dict ``{"text": ..., "position_tag": ..., "layout_type": ...}`` from
        the newer adapter, where DeepDoc's own layout classifier may tag the
        line as ``title``/``header``/``text``/etc.

    To pick markdown heading levels we look at, in order:
      1. ``layout_type`` if present (most reliable);
      2. numeric prefixes like ``1.2.3.`` (depth → level);
      3. Chinese chapter markers (``第二章``, ``一、`` …);
      4. font-size heuristics from the position tag (lines whose visual height
         is significantly larger than the document's median body line are
         very likely headings).

    The heuristics intentionally err on the side of more headings — a page
    with no structure at all reads worse than one with a few false positives.
    """

    _BULLET_PATTERN = re.compile(r"^[\s]*[•·●○▪▫■□◆◇➢✓*\-][\s]+(.+)$")
    _ORDERED_PATTERN = re.compile(r"^[\s]*(\d+)[.)、]\s+(.+)$")
    # Allow "2.1.3. NFS" AND "2.服务器设置" (no space after the dot).
    # We still require the trailing content to start with a non-space char
    # so "2.0" or "2." alone won't match.
    _NUMBERED_HEADING_PATTERN = re.compile(
        r"^(\d+(?:\.\d+){0,5})[.、．]?\s*(\S.{0,120})$"
    )
    _CHINESE_HEADING_PATTERN = re.compile(
        r"^(第[一二三四五六七八九十百千万\d]+[章节篇部回]"
        r"|[一二三四五六七八九十]+[、．.])\s*(.+)$"
    )
    _APPENDIX_HEADING_PATTERN = re.compile(r"^(附录\s*[A-Z\d一二三四五六七八九十]+)[.、．:：]?\s*(.+)?$")
    _MARKDOWN_PREFIX_PATTERN = re.compile(r"^\s*(#{1,6}\s+|[-*+]\s+|\d+\.\s+|>\s+|```)")
    _POSITION_PATTERN = re.compile(
        r"@@(\d+)\t([\d.]+)\t([\d.]+)\t([\d.]+)\t([\d.]+)##"
    )
    _CODE_START_PATTERN = re.compile(
        r"^\s*(def |class |async def |function |const |let |var |import |from |package |public |private |protected |SELECT |INSERT |UPDATE |DELETE |CREATE |WITH )",
        re.IGNORECASE,
    )
    _CODE_OPERATOR_PATTERN = re.compile(r"(\{|\}|;|=>|==|!=|<=|>=|:=|&&|\|\||</|/>)")
    _INLINE_CODE_ANCHOR_PATTERN = re.compile(
        r"\b(package\s+main|func\s+\w+\s*\(|import\s*\(|var\s+\w+\s+[*\w.]+|SELECT\s+.+\s+FROM\s+)",
        re.IGNORECASE,
    )

    # Trailing punctuation that makes a short line *not* look like a heading
    # (commas, full stops, semicolons, ellipsis, closing brackets, …).
    _NON_HEADING_TAIL = ("，", ",", "。", ";", "；", "…", "?", "？", "!", "！")

    def build_text(self, sections: list[Any]) -> str:
        parts: list[str] = []
        for section in sections:
            text = self._section_text(section)
            if text:
                parts.append(text)
        return "\n".join(parts)

    def build_markdown(self, sections: list[Any], tables: list[Any]) -> str:
        # Pass 1 — collect single-line heights so we can compute a body baseline.
        # Multi-line blocks (height > ~25) are excluded: they're paragraphs,
        # not heading candidates.
        single_line_heights: list[float] = []
        for section in sections:
            metrics = self._position_metrics(self._section_meta(section))
            if metrics and 4.0 <= metrics["height"] <= 26.0:
                single_line_heights.append(metrics["height"])
        body_size = statistics.median(single_line_heights) if single_line_heights else 0.0

        blocks: list[str] = []
        seen_title = False
        previous_kind = ""
        code_buffer: list[str] = []

        def flush_code_buffer() -> None:
            nonlocal previous_kind
            if not code_buffer:
                return
            if blocks and previous_kind != "code":
                blocks.append("")
            language = self._guess_code_language(code_buffer)
            fence = f"```{language}" if language else "```"
            blocks.append(f"{fence}\n" + "\n".join(code_buffer).rstrip() + "\n```")
            code_buffer.clear()
            previous_kind = "code"

        for section in sections:
            raw_text = self._section_raw_text(section)
            text = raw_text.strip()
            if not text:
                continue

            meta = self._section_meta(section)
            if self._looks_like_fenced_markdown(text):
                flush_code_buffer()
                block, kind = self._section_markdown(text, meta, seen_title, body_size)
                if blocks and kind != "list" and previous_kind != "list":
                    blocks.append("")
                blocks.append(block)
                previous_kind = kind
                continue

            if self._looks_like_code_line(raw_text, meta):
                code_buffer.append(raw_text.rstrip())
                continue

            flush_code_buffer()
            block, kind = self._section_markdown(text, meta, seen_title, body_size)
            if kind == "title":
                seen_title = True

            if blocks and kind != "list" and previous_kind != "list":
                blocks.append("")
            blocks.append(block)
            previous_kind = kind

        flush_code_buffer()

        table_blocks = []
        for index, table in enumerate(tables, start=1):
            rendered = self._table_text(table)
            if rendered:
                table_blocks.append(f"### Table {index}\n\n{rendered}")

        if table_blocks and blocks:
            blocks.extend(["", *table_blocks])
        elif table_blocks:
            blocks.extend(table_blocks)

        return "\n".join(blocks)

    def json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(k): self.json_safe(v) for k, v in value.items()}
        if isinstance(value, (tuple, list)):
            return [self.json_safe(item) for item in value]
        if hasattr(value, "size") and hasattr(value, "mode"):
            return {"type": "image", "size": list(value.size), "mode": value.mode}
        return str(value)

    # ------------------------------------------------------------------
    # Section unpacking
    # ------------------------------------------------------------------
    def _section_text(self, section: Any) -> str:
        return self._section_raw_text(section).strip()

    def _section_raw_text(self, section: Any) -> str:
        if isinstance(section, str):
            return section
        if isinstance(section, (tuple, list)) and section:
            return str(section[0] or "")
        if isinstance(section, dict):
            return str(section.get("text") or section.get("content") or "")
        return str(section or "")

    def _section_meta(self, section: Any) -> dict[str, Any]:
        if isinstance(section, dict):
            # Normalize: surface ``position_tag`` under the ``style`` key as
            # well so downstream heuristics have a single place to look.
            meta = dict(section)
            if "style" not in meta:
                meta["style"] = meta.get("position_tag") or meta.get("layout_type") or ""
            return meta
        if isinstance(section, (tuple, list)) and len(section) > 1:
            return {"style": str(section[1] or "")}
        return {}

    def _position_metrics(self, meta: dict[str, Any]) -> dict[str, float] | None:
        """Parse ``@@page\\tx0\\tx1\\ttop\\tbottom##`` if present.

        Returns ``{"page", "x0", "x1", "top", "bottom", "height", "width"}``
        or ``None`` if no position info is available.
        """
        for key in ("style", "position_tag"):
            value = meta.get(key)
            if not value:
                continue
            match = self._POSITION_PATTERN.search(str(value))
            if match:
                page, x0, x1, top, bottom = match.groups()
                top_f = float(top)
                bottom_f = float(bottom)
                x0_f = float(x0)
                x1_f = float(x1)
                return {
                    "page": float(page),
                    "x0": x0_f,
                    "x1": x1_f,
                    "top": top_f,
                    "bottom": bottom_f,
                    "height": max(0.0, bottom_f - top_f),
                    "width": max(0.0, x1_f - x0_f),
                }
        return None

    # ------------------------------------------------------------------
    # Markdown shaping
    # ------------------------------------------------------------------
    def _section_markdown(
        self,
        text: str,
        meta: dict[str, Any],
        seen_title: bool,
        body_size: float,
    ) -> tuple[str, str]:
        normalized = self._normalize_text(text)
        if not normalized:
            return "", "text"

        if self._looks_like_markdown(normalized):
            return normalized, "markdown"

        embedded_code = self._embedded_code_markdown(normalized)
        if embedded_code:
            return embedded_code, "code"

        layout = str(meta.get("layout_type") or "").strip().lower()
        style = str(meta.get("style") or "").strip().lower()
        metrics = self._position_metrics(meta)

        heading_level = self._heading_level(normalized, layout, style, metrics, body_size, seen_title)
        if heading_level:
            return f"{'#' * heading_level} {normalized}", "title"

        bullet = self._BULLET_PATTERN.match(normalized)
        if bullet:
            return f"- {bullet.group(1).strip()}", "list"

        ordered = self._ORDERED_PATTERN.match(normalized)
        if ordered and len(ordered.group(2).strip()) > 8:
            return f"{ordered.group(1)}. {ordered.group(2).strip()}", "list"

        if "caption" in layout or "caption" in style:
            return f"*{normalized}*", "caption"

        return normalized, "text"

    def _heading_level(
        self,
        text: str,
        layout: str,
        style: str,
        metrics: dict[str, float] | None,
        body_size: float,
        seen_title: bool,
    ) -> int | None:
        # 1. Explicit layout label from DeepDoc, if available.
        if layout in {"title", "doc title", "document title"}:
            return 1 if not seen_title else 2
        if layout in {"section title", "section header", "subtitle", "header"} or "title" in layout or "heading" in layout:
            heading_match = re.search(r"heading\s*([1-6])", layout)
            if heading_match:
                return max(1, min(6, int(heading_match.group(1))))
            return 2

        if style in {"title", "heading 1", "head 1"}:
            return 1 if not seen_title else 2
        heading_match = re.search(r"heading\s*([1-6])", style)
        if heading_match:
            return max(1, min(6, int(heading_match.group(1))))

        # 2. Numeric prefix — depth maps to level.
        numbered = self._NUMBERED_HEADING_PATTERN.match(text)
        if numbered and self._is_heading_length(text) and not self._looks_like_list_item(text):
            depth = numbered.group(1).count(".") + 1
            # 1.X -> H2, 1.X.Y -> H3, 1.X.Y.Z -> H4, …
            return max(2, min(6, depth + 1))

        # 3. Chinese chapter markers.
        if self._CHINESE_HEADING_PATTERN.match(text) and self._is_heading_length(text):
            return 2

        # 4. Appendix markers ("附录 A", "附录一").
        if self._APPENDIX_HEADING_PATTERN.match(text) and self._is_heading_length(text):
            return 2

        # 5. Trailing-colon hint ("配置示例：") — usually a sub-heading.
        if text.endswith(("：", ":")) and self._is_heading_length(text) and len(text) <= 30:
            return 3

        # 6. Font-size heuristic. Only applies when we have both a body
        # baseline and metrics for this line, and the line is a single
        # visual row (height in the normal body range, no multi-row blocks).
        if (
            metrics
            and body_size
            and 4.0 <= metrics["height"] <= 26.0
            and self._is_heading_length(text)
            and not text.endswith(self._NON_HEADING_TAIL)
            and not self._looks_like_list_item(text)
        ):
            ratio = metrics["height"] / body_size
            # H1 by font size is reserved for very large, very short lines
            # that look like a document title (no inline spaces / commas).
            if (
                ratio >= 1.8
                and len(text) <= 25
                and " " not in text
                and "，" not in text
                and "," not in text
            ):
                return 1 if not seen_title else 2
            if ratio >= 1.35 and len(text) <= 60:
                return 2
            if ratio >= 1.18 and len(text) <= 30:
                return 3

        return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _looks_like_markdown(self, text: str) -> bool:
        return bool(self._MARKDOWN_PREFIX_PATTERN.match(text)) or self._is_table_row(text)

    def _looks_like_fenced_markdown(self, text: str) -> bool:
        return text.strip().startswith("```")

    def _looks_like_code_line(self, text: str, meta: dict[str, Any]) -> bool:
        if self._looks_like_markdown(text):
            return False

        raw = text.rstrip()
        stripped = raw.strip()
        if not stripped or len(stripped) > 180:
            return False

        layout = str(meta.get("layout_type") or "").lower()
        style = str(meta.get("style") or "").lower()
        if "caption" in layout or "caption" in style or "title" in layout or "heading" in style:
            return False

        if raw[:1].isspace() and len(stripped) >= 2:
            return True
        if self._CODE_START_PATTERN.match(stripped):
            return True
        if self._CODE_OPERATOR_PATTERN.search(stripped) and not re.search(r"[\u4e00-\u9fff]{4,}", stripped):
            return True
        if stripped in {"else:", "try:", "except:", "finally:", "do", "then"}:
            return True
        if re.match(r"^(if|for|while|switch|catch|elif|else if)\s*[\(\w].*[:{]$", stripped):
            return True
        if re.match(r"^[A-Za-z_$][\w.$-]*\s*=\s*.+", stripped):
            return True
        if re.match(r"^[A-Za-z_$][\w.$-]*\(.*\)$", stripped):
            return True
        return False

    def _guess_code_language(self, lines: list[str]) -> str:
        joined = "\n".join(lines)
        if re.search(r"^\s*(def |class |from |import |async def )", joined, re.MULTILINE):
            return "python"
        if re.search(r"\b(function|const|let|var|=>|console\.log)\b", joined):
            return "javascript"
        if re.search(r"\b(public|private|protected|static|void|class)\b", joined) and ";" in joined:
            return "java"
        if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|FROM|WHERE)\b", joined, re.IGNORECASE):
            return "sql"
        if re.search(r"^\s*package\s+\w+", joined, re.MULTILINE):
            return "go"
        if joined.strip().startswith(("{", "[")):
            return "json"
        return ""

    def _embedded_code_markdown(self, text: str) -> str:
        match = self._INLINE_CODE_ANCHOR_PATTERN.search(text)
        if not match:
            return ""

        code = text[match.start():].strip()
        if len(code) < 80:
            return ""

        score = sum(
            token in code
            for token in ("func ", "package ", "import ", "var ", "sql.", "fmt.", "err :=", "db.", "SELECT ", "INSERT ")
        )
        if score < 3:
            return ""

        prefix = text[: match.start()].strip()
        language = "go" if "func " in code or "package main" in code else self._guess_code_language([code])
        formatted = self._format_inline_code(code, language)
        fence = f"```{language}" if language else "```"
        block = f"{fence}\n{formatted}\n```"
        return f"{prefix}\n\n{block}" if prefix else block

    def _format_inline_code(self, code: str, language: str) -> str:
        if language == "go":
            replacements = [
                (r"\s+(import\s*\()", r"\n\1"),
                (r"\s+(\)\s*)?(var\s+\w+)", r"\n\2"),
                (r"\s+(func\s+\w+\s*\([^)]*\)\s*\{)", r"\n\1"),
                (r"\s+((?:if|else|for)\s+[^{}]*\{)", r"\n\1"),
                (r"\s+(\}\s*else\s*\{)", r"\n\1"),
                (r"\s+(\}\s*)", r"\n\1\n"),
            ]
            for pattern, replacement in replacements:
                code = re.sub(pattern, replacement, code)
            return "\n".join(line.strip() for line in code.splitlines() if line.strip())

        return code

    def _looks_like_list_item(self, text: str) -> bool:
        """Avoid promoting catalogue-style lines like ``1.产品概述 1.1. UXDB …``
        to headings — those have multiple numeric tokens on the same row.
        """
        # Count distinct numeric prefixes that look like section numbers.
        return len(re.findall(r"(?<![\d.])\d+(?:\.\d+){1,4}\b", text)) >= 2

    def _is_heading_length(self, text: str) -> bool:
        if len(text) > 80:
            return False
        if text.endswith(("。",)):
            return False
        # A genuine heading rarely contains a Chinese full stop in the middle.
        if "。" in text[:-1]:
            return False
        # Lines with multiple period+space tend to be sentences, not headings.
        if text.count(". ") > 1:
            return False
        return True

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"[ \t　]+", " ", text.strip())

    def _is_table_row(self, text: str) -> bool:
        return text.count("|") >= 2

    def _table_text(self, table: Any) -> str:
        if isinstance(table, str):
            return self._render_table_string(table)
        if hasattr(table, "size") and hasattr(table, "mode"):
            return ""
        if self._is_coordinate_block(table):
            return ""
        if isinstance(table, (tuple, list)):
            parts = []
            for item in table:
                rendered = self._table_text(item)
                if rendered:
                    parts.append(rendered)
            return "\n\n".join(parts).strip()
        return str(table).strip()

    def _render_table_string(self, value: str) -> str:
        text = value.strip()
        if not text:
            return ""
        if "<table" in text.lower() and "</table>" in text.lower():
            rows = self._parse_html_table(text)
            if rows:
                return self._rows_to_markdown_table(rows)
        if text.startswith("<PIL.Image") or "PIL.Image.Image image" in text:
            return ""
        return text

    def _parse_html_table(self, html: str) -> list[list[str]]:
        parser = _HtmlTableParser()
        parser.feed(html)
        return parser.rows

    def _rows_to_markdown_table(self, rows: list[list[str]]) -> str:
        width = max(len(row) for row in rows)
        normalized_rows = [row + [""] * (width - len(row)) for row in rows]
        header = normalized_rows[0]
        separator = ["---"] * width
        body = normalized_rows[1:]
        rendered = [
            "| " + " | ".join(self._escape_table_cell(cell) for cell in header) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        rendered.extend("| " + " | ".join(self._escape_table_cell(cell) for cell in row) + " |" for row in body)
        return "\n".join(rendered)

    def _escape_table_cell(self, cell: str) -> str:
        return cell.replace("|", "\\|").strip()

    def _is_coordinate_block(self, value: Any) -> bool:
        if not isinstance(value, (tuple, list)) or not value:
            return False
        if all(isinstance(item, (int, float)) for item in value):
            return True
        return all(self._is_coordinate_block(item) for item in value)
