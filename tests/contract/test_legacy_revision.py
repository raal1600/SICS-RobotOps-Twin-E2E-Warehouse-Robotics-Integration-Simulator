"""Compatibility is checked against bytes captured BEFORE schema extension."""

import hashlib
import json
import shutil
from pathlib import Path

from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import ActionPlan, CommandReceipt, JobState, RobotCommand, WorldState
from robotops.scene_geometry import cell_meshes
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store, digest

FIXTURE = Path(__file__).parents[1] / "fixtures" / "legacy_v1"


def test_pre_upgrade_evidence_bytes_and_command_digest_are_preserved():
    manifest = json.loads((FIXTURE / "manifest.json").read_bytes())
    assert manifest["source_commit"] == "eaf35b499e80a5ce31b2ea3a24fbfa010bc67c98"
    for name, evidence in manifest["files"].items():
        assert hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest() == evidence["sha256"]
    command = RobotCommand.model_validate_json(
        (FIXTURE / "robot-command-original-wire.json").read_bytes()
    )
    assert digest(command) == manifest["command_digest"]
    assert command.model_dump(mode="json") == json.loads(
        (FIXTURE / "robot-command.json").read_bytes()
    )
    for model, name in [
        (WorldState, "world-before.json"),
        (WorldState, "world-after.json"),
        (ActionPlan, "action-plan.json"),
        (CommandReceipt, "receipt.json"),
    ]:
        raw = json.loads((FIXTURE / name).read_bytes())
        assert model.model_validate(raw).model_dump(mode="json") == raw
    world = json.loads((FIXTURE / "world-before.json").read_bytes())
    assert json.loads(json.dumps(cell_meshes(world))) == json.loads(
        (FIXTURE / "scene-before.json").read_bytes()
    )


def test_pre_upgrade_unknown_command_recovers_with_original_hash_and_one_effect(tmp_path):
    for name in ("runtime.db", "workflow.db"):
        shutil.copyfile(FIXTURE / "restart-snapshot" / name, tmp_path / name)
    manifest = json.loads((FIXTURE / "manifest.json").read_bytes())
    runtime = SyntheticRuntime(tmp_path / "runtime.db")
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime)
    original = store.job(manifest["job_id"])
    assert original.state == JobState.UNKNOWN_OUTCOME
    assert original.command_id == manifest["command_id"]
    recovered = engine.recover()
    assert len(recovered) == 1 and recovered[0].state == JobState.COMPLETED
    command = store.load(RobotCommand, original.command_id)
    assert digest(command) == manifest["command_digest"]
    assert runtime.apply(command).effect_count == 1
    assert sum(event.event_type == "PICK_EFFECT" for event in runtime.events()) == 1
    assert len(store.records_for_job(RobotCommand, original.job_id)) == 1
