import ast
import inspect
from pathlib import Path

import pytest

from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import (
    Fault,
    JobState,
    OrderLine,
    OrderRequest,
    RobotCommand,
    Verdict,
    WorldObservation,
)
from robotops.observation.model import ObservationModel
from robotops.verification.verifier import Verifier
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_hkm_verifier_signature_and_import_graph_exclude_private_world_access():
    signature = inspect.signature(Verifier.verify)
    assert signature.parameters["observation"].annotation is WorldObservation
    for path in Path("robotops/verification").glob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in {"WorldState", "SyntheticRuntime", "BlenderRuntime", "bpy"}
            elif isinstance(node, ast.Attribute):
                assert node.attr not in {"world", "_world"}
            elif isinstance(node, ast.ImportFrom):
                assert not any(
                    part in (node.module or "")
                    for part in ("cell.runtime", "blender", "observation.model", "hkm_geometry")
                )
            elif isinstance(node, ast.Import):
                assert not any(
                    part in alias.name
                    for alias in node.names
                    for part in ("bpy", "cell.runtime", "blender.adapter")
                )


def test_hkm_private_destination_truth_cannot_resolve_contradictory_observation(tmp_path):
    settings = Settings.hkm()
    runtime = SyntheticRuntime(tmp_path / "runtime.db", settings)
    store = Store(tmp_path / "workflow.db")
    engine = Engine(store, runtime)
    product = settings.products[0]
    order = store.intake(
        OrderRequest(
            order_id="boundary-order",
            lines=(
                OrderLine(
                    order_line_id="line",
                    product_id=product.product_id,
                    source_id=settings.source_for(product.product_id),
                    destination_id=settings.destination_id,
                ),
            ),
        ),
        "boundary-key",
    )
    job = engine.run(order.job_ids[0], Fault.DROP_ACK_AFTER_EFFECT)
    assert job.state == JobState.UNKNOWN_OUTCOME
    command = store.load(RobotCommand, job.command_id)
    receipt = runtime.recorded_journal(command.command_id)
    private_truth = runtime.world()
    assert private_truth.objects[0].location_id == settings.destination_id
    contradictory = ObservationModel(settings).observe(
        private_truth, Fault.CONTRADICTORY_OBSERVATION
    )
    assert any(
        obj.location_id == settings.destination_id
        for obj in contradictory.objects
        if obj.product_id == product.product_id
    )
    result = Verifier(settings).verify(command, contradictory, receipt)
    assert result.verdict == Verdict.INCONCLUSIVE and result.reason == "CONTRADICTORY_OBSERVATION"
    with pytest.raises(TypeError, match="WORLD_OBSERVATION_REQUIRED"):
        Verifier(settings).verify(command, private_truth, receipt)
    assert (
        engine.reconcile(job.job_id, Fault.CONTRADICTORY_OBSERVATION).state
        == JobState.REQUIRES_INTERVENTION
    )
    assert sum(event.event_type == "PICK_EFFECT" for event in runtime.events()) == 1


@pytest.mark.parametrize(
    "fault",
    [
        None,
        Fault.MISSING_OBSERVATION,
        Fault.LOW_CONFIDENCE_OBSERVATION,
        Fault.STALE_OBSERVATION,
        Fault.CONTRADICTORY_OBSERVATION,
        Fault.POSE_UNCERTAINTY,
    ],
)
def test_hkm_observation_noise_is_deterministic_and_telemetry_is_not_camera_perception(
    tmp_path, fault
):
    settings = Settings.hkm(seed=42, pose_noise_m=0.001)
    world = SyntheticRuntime(tmp_path / "runtime.db", settings).world()
    observer = ObservationModel(settings)
    first, second = observer.observe(world, fault), observer.observe(world, fault)
    assert first.objects == second.objects
    assert first.covered_locations == second.covered_locations
    assert first.sensors == second.sensors
    assert first.machine_telemetry.source == "SIMULATED_CELL_TELEMETRY"
    assert first.machine_telemetry.tool_state == second.machine_telemetry.tool_state
    assert {sensor.frame_id for sensor in first.sensors} == {"camera_overhead", "camera_side"}
    assert all(obj.evidence_source == "SYNTHETIC_OBSERVATION_MODEL" for obj in first.objects)
    assert all(not sensor.presentation_only for sensor in first.sensors)
    if fault == Fault.CONTRADICTORY_OBSERVATION:
        assert len({obj.sensor_id for obj in first.objects}) == 2
