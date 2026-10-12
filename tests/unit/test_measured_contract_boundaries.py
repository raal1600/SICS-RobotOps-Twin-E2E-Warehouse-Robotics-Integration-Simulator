import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from robotops.calibration.provenance import source_snapshot
from robotops.cell.calibration_execution import initial_machine
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import WorldState


def test_new_runtime_preconditions_remain_explicit_with_python_optimization():
    code = """
from types import SimpleNamespace
import numpy as np
from robotops.calibration.errors import CalibrationError
from robotops.calibration.service import CalibrationService
from robotops.cell.calibration_motion import controller_frames
checks = (
    (lambda: next(controller_frames(SimpleNamespace(calibration_machine=None),
        SimpleNamespace(calibrated_plan=None), np.eye(4))), 'MEASURED_MOTION_CONTEXT_REQUIRED'),
    (lambda: CalibrationService._export_captures({'records': {}}), 'INVALID_EVIDENCE_MANIFEST'),
)
for operation, expected in checks:
    try:
        operation()
    except CalibrationError as error:
        if error.code != expected:
            raise RuntimeError(error.code)
    else:
        raise RuntimeError('Runtime guard was skipped')
"""
    result = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_numerical_services_cannot_import_oracle_or_world():
    root = Path("robotops/calibration")
    forbidden = {"WorldState", "SyntheticSensorWorld", "instructor_reference", "SyntheticRuntime"}
    for name in ("geometry", "estimation", "depth", "tcp", "validation", "perception"):
        tree = ast.parse((root / f"{name}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in forbidden, (name, node.id)
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    part in (node.module or "")
                    for part in ("synthetic", "cell.runtime", "domain.models")
                )


def test_v1_v2_wire_does_not_gain_null_measured_fields(tmp_path):
    for label, settings in (("v1", Settings()), ("v2", Settings.hkm())):
        assert "calibration_command_mode" not in settings.model_dump(mode="json")
        world = SyntheticRuntime(tmp_path / f"{label}.db", settings).world()
        body = world.model_dump(mode="json")
        assert "calibration_machine" not in body
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        reconstructed = WorldState.model_validate(body)
        repeated = json.dumps(
            reconstructed.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        assert (
            hashlib.sha256(repeated.encode()).digest()
            == hashlib.sha256(canonical.encode()).digest()
        )
        with pytest.raises(ValidationError, match="MEASURED_FIELDS_REQUIRE_VERSION_3"):
            WorldState.model_validate({**body, "calibration_machine": initial_machine()})


def test_measured_command_mode_is_explicit_and_preserves_existing_settings_wire():
    assert "calibration_command_mode" not in Settings.calibration().model_dump(mode="json")
    for mode in ("tcp", "flange"):
        measured = Settings.calibration(calibration_command_mode=mode)
        assert Settings.model_validate_json(measured.model_dump_json()) == measured
        with pytest.raises(ValidationError, match="MEASURED_FIELDS_REQUIRE_VERSION_3"):
            Settings.hkm(calibration_command_mode=mode)


def test_version_three_is_not_a_way_to_bypass_profile_metadata(tmp_path):
    world = SyntheticRuntime(tmp_path / "runtime.db", Settings()).world().model_dump(mode="json")
    with pytest.raises(ValidationError, match="MEASURED_WORLD_PROFILE_REQUIRED"):
        WorldState.model_validate({**world, "schema_version": "3.0"})
    settings = Settings.calibration()
    assert settings.is_measured and not settings.is_hkm
    with pytest.raises(ValidationError, match="MEASURED_PROFILE_REQUIRES_VERSION_3"):
        Settings.model_validate({**settings.model_dump(mode="json"), "schema_version": "2.0"})


def test_calculation_source_allowlist_and_displayed_hash():
    source = source_snapshot("robotops/calibration/depth.py", "reconstruct")
    assert hashlib.sha256(source["content"].encode()).hexdigest() == source["displayed_sha256"]
    assert "def reconstruct" in source["excerpt"]
    assert source["symbol_end_line"] > source["symbol_start_line"]
    with pytest.raises(ValueError, match="SOURCE_NOT_ALLOWLISTED"):
        source_snapshot("../../.ssh/id_rsa", "secret")
    with pytest.raises(ValueError, match="SOURCE_SYMBOL_NOT_FOUND"):
        source_snapshot("robotops/calibration/depth.py", "does_not_exist")
