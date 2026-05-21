from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

import orjson

from app.core.config import get_settings
from app.models.schemas import TaskEvent, TaskRecord, TaskStatus


class TaskStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._dir = get_settings().result_dir / "tasks"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, task_id: str) -> Path:
        return self._dir / f"{task_id}.json"

    def create(self, record: TaskRecord) -> TaskRecord:
        return self.save(record)

    def save(self, record: TaskRecord) -> TaskRecord:
        with self._lock:
            payload = record.model_dump(mode="json")
            self._path(record.task_id).write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        return record

    def get(self, task_id: str) -> TaskRecord | None:
        path = self._path(task_id)
        if not path.exists():
            return None
        return TaskRecord.model_validate(orjson.loads(path.read_bytes()))

    def update(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        progress: float | None = None,
        message: str | None = None,
        error: str | None = None,
        result_path: str | None = None,
    ) -> TaskRecord:
        with self._lock:
            record = self.get(task_id)
            if record is None:
                raise KeyError(f"task not found: {task_id}")

            if status is not None:
                record.status = status
            if progress is not None:
                record.progress = max(0, min(1, progress))
            if message is not None:
                record.message = message
            if error is not None:
                record.error = error
            if result_path is not None:
                record.result_path = result_path

            record.updated_at = datetime.now(timezone.utc)
            record.events.append(
                TaskEvent(
                    at=record.updated_at,
                    status=record.status,
                    progress=record.progress,
                    message=record.message,
                )
            )
            return self.save(record)


task_store = TaskStore()
