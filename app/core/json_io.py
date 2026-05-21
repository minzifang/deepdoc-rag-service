from pathlib import Path
from uuid import uuid4

import orjson


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    tmp_path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    tmp_path.replace(path)
