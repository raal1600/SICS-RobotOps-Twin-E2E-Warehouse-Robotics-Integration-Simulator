"""Atomic presentation snapshots; bounded retry of Windows reader sharing locks."""

import json
import time
from pathlib import Path


def write_snapshot(path: Path, value: object) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    for attempt in range(50):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 49:
                raise
            time.sleep(0.01)
