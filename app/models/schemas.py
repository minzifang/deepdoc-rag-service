from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ParserMode = Literal["auto", "deepdoc", "plain"]
TaskStatus = Literal["queued", "parsing", "done", "failed"]


class DocumentCreateResponse(BaseModel):
    task_id: str
    doc_id: str
    status: TaskStatus
    filename: str


class TaskEvent(BaseModel):
    at: datetime
    status: TaskStatus
    progress: float = Field(ge=0, le=1)
    message: str = ""


class TaskRecord(BaseModel):
    task_id: str
    doc_id: str
    filename: str
    kb_id: str | None = None
    parser_mode: ParserMode
    status: TaskStatus
    progress: float = Field(default=0, ge=0, le=1)
    message: str = ""
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    result_path: str | None = None
    events: list[TaskEvent] = Field(default_factory=list)


class DocumentResult(BaseModel):
    doc_id: str
    filename: str
    parser_mode: ParserMode
    parser_used: str
    text: str
    markdown: str
    sections: list[Any] = Field(default_factory=list)
    tables: list[Any] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
