"""Standard-library catalogue access, shared with the fixed Blender process."""

import json
from pathlib import Path
from typing import Any

CATALOGUE_PATH = Path(__file__).with_name("catalogue-v1.json")

# SIMULATOR_DESIGN: bounded source-contact centering, not physical gripper accuracy.
# Kept separate from the verifier's observation/postcondition pose tolerance.
SYNTHETIC_GRASP_CONTACT_TOLERANCE_M = 0.005


def raw_catalogue() -> dict[str, Any]:
    """Return independent JSON data; callers cannot mutate a shared cached catalogue."""
    data: dict[str, Any] = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    return data
