from concurrent.futures import ThreadPoolExecutor

import pytest

from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.errors import CalibrationError
from robotops.calibration.tcp import verify_measurements
from robotops.cell.calibration_sensor import ControllerSensor
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.store import Conflict


def test_tool_measurements_are_durable_and_check_replay_never_reenables_changed_cell(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=42))
    sensor = ControllerSensor(runtime, SensorArtifacts(tmp_path / "images"))
    before = runtime.world()
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: sensor.measure_tool("same-measurement"), range(3)))
    assert results[0] == results[1] == results[2]
    measurements = results[0]
    assert runtime.world() == before  # Measuring cannot authorize or remove the board.
    assert measurements.pivot_flange_poses[0].matrix[2][3] == pytest.approx(0.47)
    assert measurements.probes[0].measured_flange_point_m == (0, 0, 0.18)
    report = verify_measurements(measurements)
    assert report.passed
    with pytest.raises(CalibrationError, match="RECOMPUTATION"):
        sensor.apply_tool_check(measurements, report.model_copy(update={"pivot_rms_mm": 99}))
    assert runtime.world() == before
    sensor.apply_tool_check(measurements, report)
    checked = runtime.world()
    assert checked.calibration_machine.tool_verification_id == measurements.measurement_id
    assert not checked.calibration_machine.board_mounted
    restored = ControllerSensor(
        SyntheticRuntime(tmp_path / "runtime.db"), SensorArtifacts(tmp_path / "images")
    )
    assert restored.measure_tool("same-measurement") == measurements
    restored.apply_tool_check(measurements, report)
    assert runtime.world() == checked
    restored.mount_board("later-board-install")
    changed = runtime.world()
    restored.apply_tool_check(measurements, report)
    assert runtime.world() == changed
    assert changed.calibration_machine.tool_verification_id is None
    assert changed.calibration_machine.board_mounted


def test_cell_changes_between_measurement_and_commit_leave_tool_blocked(tmp_path):
    runtime = SyntheticRuntime(tmp_path / "runtime.db", Settings.calibration(seed=43))
    sensor = ControllerSensor(runtime, SensorArtifacts(tmp_path / "images"))
    measurements = sensor.measure_tool("measured")
    sensor.move_camera("camera-west", "mount-change", (0.02, 0, 0), (0, 0, 0))
    with pytest.raises(Conflict, match="CELL_CHANGED_DURING_TOOL_VERIFICATION"):
        sensor.apply_tool_check(measurements, verify_measurements(measurements))
    assert runtime.world().calibration_machine.tool_verification_id is None
    with runtime.db.readonly_connect() as db:
        assert db.execute("SELECT COUNT(*) FROM calibration_tool_measurements").fetchone()[0] == 1
