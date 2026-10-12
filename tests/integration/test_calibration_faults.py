import numpy as np
import pytest

from robotops.calibration.checks import RoutineCheck
from robotops.calibration.contracts import Capture, IndependentReference
from robotops.calibration.diagnostics import InvestigationReport
from robotops.calibration.errors import CalibrationError
from robotops.calibration.faults import FaultRecord, definition
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.calibration.tcp import ToolVerification
from robotops.cell.calibration_sensor import ControllerSensor
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def test_fault_measurements_diagnose_depth_without_rewriting_extrinsics_and_tool_is_separate(
    tmp_path,
):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=37))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    service = engine.calibration
    camera = "camera-west"

    def mutation(identity):
        return Mutation(request_id=identity, expected_revision=service.store.state(camera).revision)

    service.configure(camera, Mutation(request_id="configure", expected_revision=0))
    service.acquire(camera, "fit", mutation("measure"))
    service.fit(camera, "fit", "candidate", mutation("fit"))
    validation = service.validate(camera, "candidate", "unused-final", mutation("validate"))
    report = service.report(validation.record_ids[0])
    assert report.passed, report.failures
    service.store.approve(
        camera, "candidate", report.report_id, "Simulated test operator", mutation("approve")
    )
    original = service.store.active(camera)
    for kind, failure in (
        ("tool_translation", "TCP_TRANSLATION_CHECK_FAILED"),
        ("tool_rotation", "TOOL_ORIENTATION_CHECK_FAILED"),
    ):
        service.introduce_fault(camera, kind, mutation(kind))
        assert service.store.active(camera) == original
        check = service.prepare_tool(camera, mutation(f"check-{kind}"))
        checked = service.store.record("tool-verification", check.record_ids[0], ToolVerification)
        failed_tool_check_id = checked.verification_id
        assert not checked.passed and failure in checked.failures
        assert runtime.world().calibration_machine.tool_verification_id is None
        assert service.store.active(camera).candidate.x == original.candidate.x
    service.introduce_fault(camera, "restore_tool", mutation("restore-tool"))
    service.prepare_tool(camera, mutation("tool-reverified"))
    assert runtime.world().calibration_machine.tool_verification_id is not None

    request = mutation("scale-fault")
    receipt = service.introduce_fault(camera, "depth_scale", request)
    effect_generation = runtime.world().cell.generation
    assert service.introduce_fault(camera, "depth_scale", request) == receipt
    assert runtime.world().cell.generation == effect_generation
    assert service.store.state(camera).active_artifact_id == original.artifact_id
    with pytest.raises(CalibrationError, match="SUSPECT"):
        service.store.active(camera)
    checked = service.routine_check(camera, mutation("check-scale"))
    with service.store.store.readonly_connect() as db:
        import json

        scale_report = json.loads(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='routine-check' AND id=?",
                (checked.record_ids[0],),
            ).fetchone()[0]
        )
    assert not scale_report["passed"]
    assert "SCALE_ERROR_COMPATIBLE" in scale_report["diagnostic"]["clues"]
    assert scale_report["diagnostic"]["conclusion"] == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
    assert scale_report["diagnostic"]["diagnostic_scale"] == pytest.approx(1 / 1.08, abs=0.004)
    checked_report = RoutineCheck.model_validate(scale_report)
    measured_references = tuple(
        service.store.record("reference", item.reference_id, IndependentReference)
        for item in checked_report.references
    )
    tampered = checked_report.model_copy(
        update={"check_id": "forged-pass", "passed": True, "failures": ()}
    )
    with pytest.raises(CalibrationError, match="ROUTINE_REPORT_RECOMPUTATION_MISMATCH"):
        service.store.save_routine_check(tampered, mutation("forged-routine"), measured_references)
    assert service.store.state(camera).active_validity == "SUSPECT_INVALID"
    (tmp_path / "scale-diagnostic.json").write_text(
        json.dumps(scale_report, indent=2), encoding="utf-8"
    )

    for kind in ("depth_zero", "depth_nonfinite", "units_1000", "depth_mixed"):
        service.introduce_fault(camera, kind, mutation(kind))
        result = service.routine_check(camera, mutation(f"check-{kind}"))
        with service.store.store.readonly_connect() as db:
            failed = json.loads(
                db.execute(
                    "SELECT body FROM calibration_records WHERE kind='routine-check' AND id=?",
                    (result.record_ids[0],),
                ).fetchone()[0]
            )
        assert not failed["passed"] and failed["failed_capture_ids"]
        capture = service.store.record("capture", failed["failed_capture_ids"][0], Capture)
        assert capture.sensor_fault_ids
        assert service.store.record("artifact", original.artifact_id, type(original)) == original
    service.introduce_fault(camera, "restore_sensor", mutation("restore-sensor"))
    restored = service.routine_check(camera, mutation("check-restored"))
    assert restored.state.active_validity == "SUSPECT_INVALID"  # Passing is not approval.
    with service.store.store.readonly_connect() as db:
        result = json.loads(
            db.execute(
                "SELECT body FROM calibration_records WHERE kind='routine-check' AND id=?",
                (restored.record_ids[0],),
            ).fetchone()[0]
        )
    assert result["passed"], result
    assert restored.state.active_artifact_id == original.artifact_id

    # Investigations read measured evidence, not the injected fault's instructor label.
    for kind, identity, clue in (
        ("routine-check", checked_report.check_id, "SCALE_ERROR_COMPATIBLE"),
        ("tool-verification", failed_tool_check_id, "INDEPENDENT_TOOL_CHECK_FAILED"),
        ("routine-check", result["check_id"], "INSUFFICIENT_EVIDENCE"),
    ):
        request = mutation(f"investigate-{identity}")
        before = service.store.state(camera)
        inspected = service.investigate(camera, kind, identity, request)
        assert service.investigate(camera, kind, identity, request) == inspected
        report = service.store.record("investigation", inspected.record_ids[0], InvestigationReport)
        assert clue in {item.code for item in report.clues}
        assert report.conclusion == "INSUFFICIENT_EVIDENCE / UNKNOWN_CAUSE"
        assert inspected.state.active_validity == before.active_validity
        assert inspected.state.active_artifact_id == original.artifact_id
        assert inspected.state.limits == before.limits
        assert "fault_id" not in report.calculation.inputs
    bundle = service.export(tmp_path / "investigation-evidence")
    reproduced = reproduce(bundle.parent)
    assert reproduced["passed"], reproduced
    assert len(reproduced["investigation_results"]) == 3


@pytest.mark.parametrize(
    "kind", ["range_as_z", "depth_registration", "depth_occluded", "rgb_crop", "sensor_noise"]
)
def test_faults_change_real_sensor_artifacts_and_survive_restart(tmp_path, kind):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=59))
    engine = Engine(Store(tmp_path / "workflow.db"), runtime)
    sensor = engine.calibration.sensor
    normal = sensor.fresh(("camera-west",), "comparison").captures[0]
    before_rgb = sensor.artifacts.read_rgb(normal.rgb)
    before_depth = sensor.artifacts.read_depth(normal.depth)
    fault = FaultRecord(
        fault_id=f"fault-{kind}", camera_id="camera-west", definition=definition(kind)
    )
    sensor.apply_fault(fault)
    changed = sensor.fresh(("camera-west",), "comparison").captures[0]
    assert changed.sensor_fault_ids == (fault.fault_id,)
    if kind == "rgb_crop":
        assert not np.array_equal(sensor.artifacts.read_rgb(changed.rgb), before_rgb)
        assert np.array_equal(sensor.artifacts.read_depth(changed.depth), before_depth)
    else:
        assert not np.array_equal(sensor.artifacts.read_depth(changed.depth), before_depth)
    # The same immutable sensor identity reproduces the same corrupted arrays after restart.
    restored = ControllerSensor(SyntheticRuntime(tmp_path / "runtime.db"), sensor.artifacts)
    again = restored.fresh(("camera-west",), "comparison").captures[0]
    assert again.rgb == changed.rgb and again.depth == changed.depth
    assert again.configuration_fingerprint == normal.configuration_fingerprint
