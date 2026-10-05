"""Regenerate committed wire schemas; CI compares rather than silently updating."""

import json
import tempfile
from pathlib import Path

from apps.api.app import create_app
from apps.api.test_sessions import TEST_SCHEMAS
from robotops.blender.visualization import VISUAL_SCHEMAS
from robotops.domain.models import SCHEMAS
from robotops.integration.models import (
    AuthorizationDecision,
    AuthorizeStage,
    CreateSession,
    ExecutionSession,
    ExecutionStep,
    PendingAuthorization,
    ProtocolTrace,
    SourceReference,
)
from robotops.robotics.catalogue import CATALOGUE_SCHEMAS
from robotops.robotics.models import ROBOTICS_SCHEMAS
from robotops.workflow.store import Store


def export() -> None:
    directory = Path("contracts/schemas")
    directory.mkdir(parents=True, exist_ok=True)
    integration_schemas = (
        AuthorizationDecision,
        AuthorizeStage,
        CreateSession,
        ExecutionSession,
        ExecutionStep,
        PendingAuthorization,
        ProtocolTrace,
        SourceReference,
    )
    for schema in (
        *SCHEMAS,
        *VISUAL_SCHEMAS,
        *TEST_SCHEMAS,
        *ROBOTICS_SCHEMAS,
        *CATALOGUE_SCHEMAS,
        *integration_schemas,
    ):
        (directory / f"{schema.__name__}.json").write_text(
            json.dumps(schema.model_json_schema(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    with tempfile.TemporaryDirectory() as temporary:
        spec = create_app(Store(Path(temporary) / "schema.db")).openapi()
    Path("contracts/openapi.json").write_text(
        json.dumps(spec, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    export()
