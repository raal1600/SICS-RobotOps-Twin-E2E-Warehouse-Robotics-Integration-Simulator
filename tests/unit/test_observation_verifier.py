import ast
from pathlib import Path

import pytest

from robotops.brain.deterministic import DeterministicBrain, parse_structured_output
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import RobotCommand, Verdict
from robotops.observation.model import ObservationModel
from robotops.verification.verifier import Verifier
from robotops.workflow.store import Store


def test_verifier_has_no_ground_truth_dependency():
    for path in [
        Path("robotops/verification/verifier.py"),
        Path("robotops/observation/quality.py"),
    ]:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in {"WorldState", "SyntheticRuntime", "BlenderRuntime", "bpy"}
            if isinstance(node, ast.Attribute):
                assert node.attr != "world"
            if isinstance(node, ast.ImportFrom):
                assert not any(
                    term in (node.module or "")
                    for term in ["cell.runtime", "blender", "observation.model"]
                )


def test_deterministic_brain_and_strict_model_boundary(tmp_path, order_request):
    store = Store(tmp_path / "s.db")
    runtime = SyntheticRuntime(tmp_path / "r.db")
    job = store.job(store.intake(order_request, "key").job_ids[0])
    obs = ObservationModel().observe(runtime.world())
    dest = runtime.world().locations[1]
    brain = DeterministicBrain()
    a = brain.plan(job, obs, dest)
    b = brain.plan(job, obs, dest)
    assert a == b
    assert parse_structured_output(a.model_dump_json()) == a
    with pytest.raises(ValueError):
        parse_structured_output('{"exec":"move_anything()"}')
    with pytest.raises(TypeError, match="WORLD_OBSERVATION_REQUIRED"):
        Verifier().verify(RobotCommand(**a.model_dump(), command_id="c"), runtime.world(), None)


def test_missing_journal_and_contradictory_journal_are_inconclusive(tmp_path, order_request):
    store = Store(tmp_path / "s.db")
    runtime = SyntheticRuntime(tmp_path / "r.db")
    job = store.job(store.intake(order_request, "key").job_ids[0])
    observer = ObservationModel()
    plan = DeterministicBrain().plan(
        job, observer.observe(runtime.world()), runtime.world().locations[1]
    )
    command = RobotCommand(**plan.model_dump(), command_id="command")
    receipt = runtime.apply(command)
    obs = observer.observe(runtime.world())
    assert Verifier().verify(command, obs, None).verdict == Verdict.INCONCLUSIVE
    assert (
        Verifier()
        .verify(command, obs, receipt.model_copy(update={"payload_hash": "wrong"}))
        .verdict
        == Verdict.INCONCLUSIVE
    )
