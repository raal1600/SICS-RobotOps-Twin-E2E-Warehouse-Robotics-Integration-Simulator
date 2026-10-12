"""Analytical rule-gate fixtures; no inference of statistical confidence from residuals."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from test_calibration_depth_tcp import measured_point, small_camera

from robotops.calibration.agreement import CameraAgreement
from robotops.calibration.contracts import ArtifactRef, Limits, SurfaceDetection, Transform
from robotops.calibration.errors import CalibrationError
from robotops.calibration.measurement_quality import assess_measurement
from robotops.calibration.runtime_contracts import ArtifactBinding, CalibratedObject
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import ObservedObject, Pose
from robotops.observation.model import ObservationModel


def analytical_gate_inputs():
    point = measured_point()
    detection = SurfaceDetection(
        capture_id="measured",
        camera_id=point.camera_id,
        method="red_cube_top",
        selected_rgb_pixel=point.selected_rgb_pixel,
        selected_pixel_count=50,
        mask=ArtifactRef(
            path="mask.npy", sha256="0" * 64, media_type="application/x-npy", shape=(9, 9)
        ),
    )
    agreement = CameraAgreement(
        agreement_id="overlap",
        primary_camera=point.camera_id,
        secondary_camera="second",
        primary_artifact_id="approved",
        secondary_artifact_id="approved-second",
        primary_point_m=point.point,
        secondary_point_m=(1, 2.601, 5),
        difference_mm=1,
        limit_mm=10,
        shared_mount_identity=None,
        mounting_translation_mm=None,
        mounting_rotation_deg=None,
        passed=True,
        failures=(),
    )
    # Only the numerical gate inputs are isolated here. Integration tests supply actual immutable approvals.
    limits = Limits()
    artifact = SimpleNamespace(
        artifact_id="approved",
        candidate=SimpleNamespace(
            camera=small_camera(),
            x=Transform.model_validate(point.calculation.inputs["x"]),
            limits_fingerprint=limits.fingerprint(),
        ),
        validation=SimpleNamespace(passed=True, reference_max_mm=3.0),
    )
    return point, detection, agreement, artifact, limits


def test_measured_gates_report_actual_numbers_without_fabricated_probabilities():
    point, detection, agreement, artifact, limits = analytical_gate_inputs()
    checked = assess_measurement(point, detection, agreement, artifact, limits)
    assert checked.passed and not checked.failures
    assert checked.correspondence_error_px == pytest.approx(0)
    assert checked.overlap_difference_mm == 1 and checked.overlap_limit_mm == 10
    assert checked.validation_reference_max_mm == 3 and checked.validation_limit_mm == 5
    assert checked.confidence_estimate == checked.point_uncertainty_estimate == "NOT_ESTIMATED"
    failing = assess_measurement(
        point,
        detection,
        agreement.model_copy(
            update={"difference_mm": 11, "passed": False, "failures": ("CAMERA_POINTS_DISAGREE",)}
        ),
        artifact,
        limits,
    )
    assert not failing.passed and failing.failures == ("CAMERA_AGREEMENT_FAILED",)
    with pytest.raises(CalibrationError, match="INPUT_BINDING"):
        assess_measurement(
            point,
            detection.model_copy(update={"selected_rgb_pixel": (0, 0)}),
            agreement,
            artifact,
            limits,
        )
    missing = point.model_copy(
        update={"calculation": point.calculation.model_copy(update={"outputs": {}})}
    )
    with pytest.raises(CalibrationError, match="CORRESPONDENCE_MISSING"):
        assess_measurement(missing, detection, agreement, artifact, limits)


def test_v3_unknown_statistics_are_explicit_and_old_measured_wire_is_not_relabelled():
    point, detection, agreement, artifact, limits = analytical_gate_inputs()
    checked = assess_measurement(point, detection, agreement, artifact, limits)
    measured = CalibratedObject(
        binding=ArtifactBinding(
            camera_id=point.camera_id,
            artifact_id="approved",
            artifact_fingerprint="fixture",
            camera_configuration_fingerprint=point.configuration_fingerprint,
            capture_id=detection.capture_id,
        ),
        surface_point=point,
        measurement_quality=checked,
    )
    obj = ObservedObject(
        schema_version="3.0",
        product_id="cube",
        location_id="source",
        pose=Pose(position=(1, 2.6, 4.96)),
        confidence=None,
        uncertainty_m=None,
        calibrated_object=measured,
    )
    assert obj.model_dump()["confidence"] is None and obj.model_dump()["uncertainty_m"] is None
    for field, value in (("confidence", 0.99), ("uncertainty_m", 0.003)):
        with pytest.raises(ValidationError, match="NOT_STATISTICAL_ESTIMATES"):
            ObservedObject.model_validate({**obj.model_dump(), field: value})
    historical = measured.model_dump()
    historical.pop("measurement_quality")
    old = ObservedObject.model_validate(
        {
            **obj.model_dump(),
            "confidence": 0.99,
            "uncertainty_m": 0.003,
            "calibrated_object": historical,
        }
    )
    assert old.calibrated_object.measurement_quality is None
    assert "measurement_quality" not in old.model_dump()["calibrated_object"]
    assert old.confidence == 0.99  # Saved fields remain original, with no new statistical claim.
    with pytest.raises(ValidationError, match="POINT_BINDING"):
        CalibratedObject.model_validate(
            {
                **measured.model_dump(),
                "measurement_quality": checked.model_copy(update={"capture_id": "different"}),
            }
        )


@pytest.mark.parametrize("settings", [Settings(), Settings.hkm()])
def test_legacy_observations_keep_numeric_quality_and_reject_unknown_values(tmp_path, settings):
    observation = ObservationModel(settings).observe(
        SyntheticRuntime(tmp_path / "runtime.db", settings).world()
    )
    obj = observation.objects[0]
    saved = obj.model_dump_json()
    assert ObservedObject.model_validate_json(saved).model_dump_json() == saved
    for name in ("confidence", "uncertainty_m"):
        with pytest.raises(ValidationError, match="LEGACY_OBSERVATION_REQUIRES_NUMERIC_QUALITY"):
            ObservedObject.model_validate({**obj.model_dump(), name: None})
