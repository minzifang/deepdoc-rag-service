import logging
from pathlib import Path

import orjson
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile

from app.core.config import get_settings
from app.core.jobs import create_task_record, submit_parse_job
from app.core.json_io import write_json_atomic
from app.core.task_store import task_store
from app.models.schemas import DocumentCreateResponse, DocumentResult, ParserMode, TaskRecord
from app.services.format_service import FormatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/documents", response_model=DocumentCreateResponse)
async def create_document(
    file: UploadFile = File(...),
    kb_id: str | None = Form(default=None),
    parser_mode: ParserMode | None = Form(default=None),
    from_page: int = Form(default=0),
    to_page: int | None = Form(default=None),
) -> DocumentCreateResponse:
    settings = get_settings()
    mode = parser_mode or settings.default_parser_mode

    record = create_task_record(file.filename or "document", mode, kb_id)
    doc_dir = settings.upload_dir / record.doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "document").name
    file_path = doc_dir / safe_name

    size = 0
    with file_path.open("wb") as out:
        while file_chunk := await file.read(1024 * 1024):
            size += len(file_chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                raise HTTPException(status_code=413, detail=f"file too large, max {settings.max_upload_mb} MB")
            out.write(file_chunk)

    submit_parse_job(record.task_id, file_path, from_page, to_page)
    return DocumentCreateResponse(
        task_id=record.task_id,
        doc_id=record.doc_id,
        status=record.status,
        filename=record.filename,
    )


@router.get("/tasks/{task_id}", response_model=TaskRecord)
def get_task(task_id: str) -> TaskRecord:
    record = task_store.get(task_id)
    if record is None:
        raise HTTPException(status_code=404, detail="task not found")
    return record


@router.get("/documents/{doc_id}/result", response_model=DocumentResult)
def get_document_result(doc_id: str) -> DocumentResult:
    path = get_settings().result_dir / f"{doc_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="document result not found")

    payload = orjson.loads(path.read_bytes())

    # Live-rebuild markdown/text from sections+tables with the current
    # FormatService. Historic results were produced by an older formatter
    # that emitted nearly no headings; this transparent upgrade means an
    # existing document immediately renders correctly without re-parsing
    # the source PDF.
    sections = payload.get("sections") or []
    tables = payload.get("tables") or []
    if sections:
        try:
            formatter = FormatService()
            new_markdown = formatter.build_markdown(sections, tables)
            new_text = formatter.build_text(sections)
            if (new_markdown and new_markdown != payload.get("markdown")) or (
                new_text and new_text != payload.get("text")
            ):
                payload["markdown"] = new_markdown
                payload["text"] = new_text
                try:
                    write_json_atomic(path, payload)
                except OSError as write_error:
                    logger.warning("failed to persist re-formatted result for %s: %s", doc_id, write_error)
        except Exception:  # pragma: no cover — formatter must never break GET
            logger.exception("re-format failed for %s, returning stored markdown as-is", doc_id)

    return DocumentResult.model_validate(payload)


@router.get("/documents/{doc_id}/markdown")
def get_document_markdown(doc_id: str) -> Response:
    result = get_document_result(doc_id)
    return Response(content=result.markdown, media_type="text/markdown; charset=utf-8")
