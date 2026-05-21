from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import orjson

from app.core.config import get_settings
from app.core.task_store import task_store
from app.models.schemas import DocumentResult, ParserMode, TaskRecord
from app.services.format_service import FormatService
from app.services.parser_service import ParserService


executor = ThreadPoolExecutor(max_workers=max(1, get_settings().app_workers))


def create_task_record(filename: str, parser_mode: ParserMode, kb_id: str | None) -> TaskRecord:
    now = datetime.now(timezone.utc)
    doc_id = uuid4().hex
    task_id = uuid4().hex
    return task_store.create(
        TaskRecord(
            task_id=task_id,
            doc_id=doc_id,
            filename=filename,
            kb_id=kb_id,
            parser_mode=parser_mode,
            status="queued",
            progress=0,
            message="queued",
            created_at=now,
            updated_at=now,
        )
    )


def submit_parse_job(
    task_id: str,
    file_path: Path,
    from_page: int,
    to_page: int | None,
) -> None:
    executor.submit(_run_parse_job, task_id, file_path, from_page, to_page)


def _run_parse_job(
    task_id: str,
    file_path: Path,
    from_page: int,
    to_page: int | None,
) -> None:
    record = task_store.get(task_id)
    if record is None:
        return

    def progress(value: float, message: str) -> None:
        task_store.update(task_id, status="parsing", progress=value, message=message)

    try:
        task_store.update(task_id, status="parsing", progress=0.05, message="parse job started")
        parser_used, sections, tables = ParserService().parse(
            file_path,
            record.filename,
            record.parser_mode,
            from_page,
            to_page,
            progress,
        )

        formatter = FormatService()
        text = formatter.build_text(sections)
        markdown = formatter.build_markdown(sections, tables)

        result = DocumentResult(
            doc_id=record.doc_id,
            filename=record.filename,
            parser_mode=record.parser_mode,
            parser_used=parser_used,
            text=text,
            markdown=markdown,
            sections=formatter.json_safe(sections),
            tables=formatter.json_safe(tables),
            metadata={
                "kb_id": record.kb_id,
                "source_path": str(file_path),
                "from_page": from_page,
                "to_page": to_page,
            },
        )
        result_path = get_settings().result_dir / f"{record.doc_id}.json"
        result_path.write_bytes(orjson.dumps(result.model_dump(mode="json"), option=orjson.OPT_INDENT_2))
        task_store.update(
            task_id,
            status="done",
            progress=1,
            message="parse done",
            result_path=str(result_path),
        )
    except Exception as exc:
        task_store.update(task_id, status="failed", progress=1, message="failed", error=repr(exc))
