"""Regenerate committed wire schemas; CI compares rather than silently updating."""

import json
from pathlib import Path

from robotops.domain.models import SCHEMAS


def export() -> None:
    directory = Path("contracts/schemas")
    directory.mkdir(parents=True, exist_ok=True)
    for schema in SCHEMAS:
        (directory / f"{schema.__name__}.json").write_text(
            json.dumps(schema.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    export()
