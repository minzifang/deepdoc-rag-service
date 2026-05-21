from typing import Any


class FormatService:
    def build_text(self, sections: list[Any]) -> str:
        parts: list[str] = []
        for section in sections:
            text = self._section_text(section)
            if text:
                parts.append(text)
        return "\n".join(parts)

    def build_markdown(self, sections: list[Any], tables: list[Any]) -> str:
        text = self.build_text(sections)
        table_blocks = []
        for index, table in enumerate(tables, start=1):
            rendered = self._table_text(table)
            if rendered:
                table_blocks.append(f"### Table {index}\n\n{rendered}")
        if table_blocks:
            return text + "\n\n" + "\n\n".join(table_blocks)
        return text

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

    def _section_text(self, section: Any) -> str:
        if isinstance(section, str):
            return section.strip()
        if isinstance(section, (tuple, list)) and section:
            return str(section[0] or "").strip()
        if isinstance(section, dict):
            return str(section.get("text") or section.get("content") or "").strip()
        return str(section or "").strip()

    def _table_text(self, table: Any) -> str:
        if isinstance(table, str):
            return table.strip()
        if isinstance(table, (tuple, list)):
            return "\n".join(str(item) for item in table if item and not hasattr(item, "size")).strip()
        return str(table).strip()
