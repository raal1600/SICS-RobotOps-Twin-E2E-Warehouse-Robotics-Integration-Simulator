"""Public capture plans and measured quality; no hidden camera or mounting inputs."""

import hashlib
from collections.abc import Sequence
from typing import Literal

import numpy as np
from scipy.spatial.transform import Rotation

from robotops.calibration.configuration import framed
from robotops.calibration.contracts import (
    Board,
    Camera,
    Capture,
    Coverage,
    Id,
    Limits,
    MeasurementRejection,
    PoseSample,
    Record,
    Transform,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import coverage

CaptureScenario = Literal[
    "varied", "repeated", "single_axis", "near_frontal", "timestamp_skew", "unsettled"
]


def scenario_options() -> tuple[dict[str, str], ...]:
    return (
        {
            "value": "varied",
            "label": "Varied, settled measurements",
            "detail": "Vary position, depth and rotations about multiple axes.",
        },
        {
            "value": "repeated",
            "label": "Repeat one pose",
            "detail": "Capture the same pose 18 times to demonstrate why image count alone is weak evidence.",
        },
        {
            "value": "single_axis",
            "label": "Rotate about one axis only",
            "detail": "Vary positions but use only one rotation axis; inspect the missing rotational diversity.",
        },
        {
            "value": "near_frontal",
            "label": "Nearly frontal board views",
            "detail": "Use a fixed nominal frontal pose to expose weak depth/tilt information and possible competing planar poses. The actual image solver decides; ambiguity is not forced.",
        },
        {
            "value": "timestamp_skew",
            "label": "Depth timestamps 100 ms late",
            "detail": "Save and reject captures whose RGB/depth timestamps exceed the frozen alignment limit.",
        },
        {
            "value": "unsettled",
            "label": "Capture before settling",
            "detail": "The simulated controller reports unsettled captures; save their rejection instead of using them to fit.",
        },
    )


class CapturePlan(Record):
    plan_id: Id
    dataset_id: Id
    camera_id: Id
    camera_fingerprint: str
    board_fingerprint: str
    scenario: CaptureScenario
    flange_poses: tuple[Transform, ...]
    settled: bool
    timestamp_skew_s: float
    scope: str = (
        "Planned synthetic flange inputs; not executed poses or calibration evidence until captured"
    )


class AcquisitionReport(Record):
    report_id: Id
    plan_id: Id
    dataset_id: Id
    camera_id: Id
    capture_count: int
    limits_fingerprint: str
    accepted_capture_ids: tuple[Id, ...]
    rejections: tuple[MeasurementRejection, ...]
    coverage: Coverage
    ready_to_fit: bool
    next_action: str
    scope: str = "Measurement quality only; does not create a candidate or approve calibration"


def make_plan(
    dataset_id: str,
    camera: Camera,
    board: Board,
    poses: tuple[Transform, ...],
    scenario: CaptureScenario = "varied",
    *,
    settled: bool = True,
    timestamp_skew_s: float = 0,
) -> CapturePlan:
    if not poses or any((pose.source, pose.destination) != ("f", "b") for pose in poses):
        raise CalibrationError("INVALID_CAPTURE_PLAN")
    if scenario == "repeated":
        matrix = np.array(poses[0].matrix)
        matrix[:3, :3] = np.eye(3)
        poses = (framed(matrix, "f", "b"),) * len(poses)
    elif scenario == "single_axis":
        # Preserve varied positions while rotating only around base z. This
        # demonstrates that translation coverage cannot replace rotation diversity.
        changed = []
        for index, pose in enumerate(poses):
            matrix = np.array(pose.matrix)
            matrix[:3, :3] = Rotation.from_euler("z", 0.36 * np.sin(index * 1.37)).as_matrix()
            changed.append(framed(matrix, "f", "b"))
        poses = tuple(changed)
    elif scenario == "near_frontal":
        # A declared experiment from the nominal cell layout, not an oracle lookup.
        # It need not remain frontal after a sensor moves. Actual images and the
        # unchanged IPPE/conditioning gates determine acceptance or rejection.
        rotations = {"camera-west": (0.82, -0.54, 0), "camera-east": (0.82, 0.54, 0)}
        if camera.camera_id not in rotations:
            raise CalibrationError("NO_NOMINAL_FRONTAL_EXPERIMENT_FOR_CAMERA")
        matrix = np.eye(4)
        matrix[:3, :3] = Rotation.from_euler("xyz", rotations[camera.camera_id]).as_matrix()
        matrix[:3, 3] = (0, 0, 0.65)
        poses = (framed(matrix, "f", "b"),) * len(poses)
    elif scenario == "timestamp_skew":
        timestamp_skew_s = 0.1
    elif scenario == "unsettled":
        settled = False
    return CapturePlan(
        plan_id="plan-"
        + hashlib.sha256(f"{camera.camera_id}/{dataset_id}".encode()).hexdigest()[:32],
        dataset_id=dataset_id,
        camera_id=camera.camera_id,
        camera_fingerprint=camera.fingerprint(),
        board_fingerprint=board.fingerprint(),
        scenario=scenario,
        flange_poses=poses,
        settled=settled,
        timestamp_skew_s=timestamp_skew_s,
    )


def assess(
    plan: CapturePlan,
    captures: Sequence[Capture],
    samples: Sequence[PoseSample],
    rejected: Sequence[MeasurementRejection],
    camera: Camera,
    limits: Limits,
) -> AcquisitionReport:
    identities = {capture.capture_id for capture in captures}
    sample_ids = {sample.capture_id for sample in samples}
    rejection_ids = {item.capture_id for item in rejected}
    if (
        len(captures) != len(plan.flange_poses)
        or len(identities) != len(captures)
        or sample_ids & rejection_ids
        or sample_ids | rejection_ids != identities
        or len(sample_ids) != len(samples)
        or len(rejection_ids) != len(rejected)
    ):
        raise CalibrationError("ACQUISITION_DECISION_SCOPE_MISMATCH")
    if camera.fingerprint() != plan.camera_fingerprint or any(
        capture.camera_id != plan.camera_id
        or capture.dataset_id != plan.dataset_id
        or capture.configuration_fingerprint != plan.camera_fingerprint
        or capture.board_fingerprint != plan.board_fingerprint
        for capture in captures
    ):
        raise CalibrationError("ACQUISITION_CONFIGURATION_CHANGED")
    measured_coverage = coverage(samples, camera, limits)
    ready = not measured_coverage.failures
    return AcquisitionReport(
        report_id="quality-" + plan.plan_id.removeprefix("plan-"),
        plan_id=plan.plan_id,
        dataset_id=plan.dataset_id,
        camera_id=plan.camera_id,
        capture_count=len(captures),
        limits_fingerprint=limits.fingerprint(),
        accepted_capture_ids=tuple(sample.capture_id for sample in samples),
        rejections=tuple(rejected),
        coverage=measured_coverage,
        ready_to_fit=ready,
        next_action="Estimate an inactive candidate from these measurements."
        if ready
        else "Inspect rejected captures and pose coverage. Start new measurements with varied, settled, time-aligned poses.",
    )
