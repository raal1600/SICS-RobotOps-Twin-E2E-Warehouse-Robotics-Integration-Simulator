"""Read-only geometry from saved measurements; never used to authorize a command."""

from typing import Literal

import numpy as np

from robotops.blender.visualization import VisualCamera, VisualObject, VisualScene
from robotops.calibration.acquisition import CapturePlan
from robotops.calibration.contracts import (
    Candidate,
    Capture,
    PoseSample,
    Record,
    ReferenceValidation,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import points
from robotops.calibration.tcp import TargetPose
from robotops.calibration.visualization import _box, axes, segment


class CapturePresentation(Record):
    capture_id: str
    camera_id: str
    capture_fingerprint: str
    scene: VisualScene
    scope: str = (
        "SAVED_SYNTHETIC_PRESENTATION: reported flange/TCP with physical simulator camera/board layout. "
        "Instructor geometry only; not calibration/perception input. Robot-report noise can differ "
        "from the physical pose used to render pixels. This is not a new robot movement."
    )


class EvidenceGeometry(Record):
    title: str
    scope: str
    frame: Literal["b"] = "b"
    unit: Literal["m"] = "m"
    objects: tuple[VisualObject, ...] = ()
    scene: VisualScene | None = None
    viewing_cameras: tuple[VisualCamera, ...] = ()
    numbers: dict[str, object]


def frame_evidence(objects: list[VisualObject]) -> tuple[VisualCamera, ...]:
    """Presentation framing only. Never move/re-scale a measured point or error vector."""
    if not objects:
        return ()
    centers = np.array([item.position for item in objects])
    low, high = centers.min(axis=0), centers.max(axis=0)
    center = (low + high) / 2
    # Bounding sphere fits the 42-degree vertical view, including marker extents.
    radius = max(float(np.linalg.norm(high - low)) / 2 + 0.03, 0.1)
    distance = radius / np.sin(np.deg2rad(21)) * 1.2
    direction = np.array([1.0, -1.4, 1.0])
    position = center + direction / np.linalg.norm(direction) * distance
    return (
        VisualCamera(
            name="Camera/OperatorOverview",
            position=tuple(position),
            target=tuple(center),
            role="PRESENTATION",
            frame_id="robot-base",
            calibration_version="inspection-only",
            camera_model_version="evidence-framing-v1",
        ),
    )


def capture_geometry(saved: CapturePresentation, capture: Capture) -> EvidenceGeometry:
    if saved.capture_fingerprint != capture.fingerprint() or saved.capture_id != capture.capture_id:
        raise CalibrationError("CAPTURE_PRESENTATION_BINDING_MISMATCH")
    return EvidenceGeometry(
        title="Saved board capture · " + capture.camera_id,
        scope="Instructor geometry from the saved capture. Robot pose follows its recorded report; camera and board layout come from the synthetic world. Small report noise remains. This view cannot move the robot or approve calibration.",
        scene=saved.scene,
        numbers={
            "capture_id": capture.capture_id,
            "camera_id": capture.camera_id,
            "reported_T_b_f": capture.t_b_f.model_dump(mode="json"),
            "admitted": capture.admitted,
            "rejection_codes": capture.rejection_codes,
            "rgb_sha256": capture.rgb.sha256,
            "depth_sha256": capture.depth.sha256,
            "presentation_scope": saved.scope,
        },
    )


def pose_geometry(plan: CapturePlan, samples: tuple[PoseSample, ...]) -> EvidenceGeometry:
    accepted = {sample.capture_id for sample in samples}
    objects = []
    rows = []
    for index, pose in enumerate(plan.flange_poses):
        identity = f"{plan.dataset_id}-{plan.camera_id}-{index:03d}"
        position = np.array(pose.matrix)[:3, 3]
        included = identity in accepted
        objects.append(
            _box(
                f"Inspection/pose-{index}",
                position,
                (0.012, 0.012, 0.012),
                (0.3, 0.85, 0.65) if included else (0.95, 0.65, 0.25),
            )
        )
        objects.extend(axes(f"Inspection/pose-{index}", np.array(pose.matrix), 0.025))
        rows.append(
            {
                "capture_id": identity,
                "accepted_board_pose": included,
                "planned_T_b_f": pose.model_dump(mode="json"),
            }
        )
    return EvidenceGeometry(
        title="Capture plan and accepted measurements",
        scope="Planned poses, not continuous robot motion. Teal cubes: accepted image pose; amber: not accepted. XYZ axes remain red/green/blue. Selection never acquires images or approves calibration.",
        objects=tuple(objects),
        viewing_cameras=frame_evidence(objects),
        numbers={"plan_id": plan.plan_id, "scenario": plan.scenario, "poses": rows},
    )


def sample_geometry(sample: PoseSample, candidate: Candidate) -> EvidenceGeometry:
    if (
        sample.camera_id != candidate.camera.camera_id
        or sample.board_fingerprint != candidate.board.fingerprint()
    ):
        raise CalibrationError("SAMPLE_CANDIDATE_CONFIGURATION_MISMATCH")
    robot_chain = np.array(sample.t_b_f.matrix) @ np.array(candidate.y.matrix)
    image_chain = np.array(candidate.x.matrix) @ np.array(sample.t_c_t.matrix)
    robot_points = points(robot_chain, np.array(sample.object_points_m))
    image_points = points(image_chain, np.array(sample.object_points_m))
    objects = axes("Inspection/reported-flange", np.array(sample.t_b_f.matrix), 0.08)
    objects += axes("Inspection/estimated-board-chain", robot_chain, 0.08)
    for index, (robot, image) in enumerate(zip(robot_points, image_points, strict=True)):
        objects += [
            _box(
                f"Inspection/robot-corner-{index}", robot, (0.004, 0.004, 0.004), (0.3, 0.85, 0.65)
            ),
            _box(f"Inspection/image-corner-{index}", image, (0.004, 0.004, 0.004), (1, 0.6, 0.2)),
        ]
        if np.linalg.norm(robot - image) > 1e-10:
            objects.append(
                segment(f"Inspection/chain-error-{index}", robot, image, (1, 0.5, 0.2), 0.0015)
            )
    return EvidenceGeometry(
        title="Measured board versus robot chain",
        scope="Estimated geometry: A Y board corners in teal, X B image-derived corners in amber. Error vectors are actual length (1:1). These estimates do not move the physical board or cameras.",
        objects=tuple(objects),
        viewing_cameras=frame_evidence(objects),
        numbers={
            "capture_id": sample.capture_id,
            "candidate_id": candidate.candidate_id,
            "A_Y": robot_chain.tolist(),
            "X_B": image_chain.tolist(),
            "robot_points_b_m": robot_points.tolist(),
            "image_points_b_m": image_points.tolist(),
            "error_vectors_m": (image_points - robot_points).tolist(),
        },
    )


def reference_geometry(
    references: tuple[ReferenceValidation, ...], identity: str
) -> EvidenceGeometry:
    objects = []
    for index, reference in enumerate(references):
        expected, measured = (
            np.array(reference.expected_base_m),
            np.array(reference.predicted_base_m),
        )
        objects += [
            _box(
                f"Inspection/reference-{index}", expected, (0.008, 0.008, 0.008), (0.3, 0.85, 0.65)
            ),
            _box(f"Inspection/predicted-{index}", measured, (0.005, 0.005, 0.005), (1, 0.6, 0.2)),
        ]
        if np.linalg.norm(measured - expected) > 1e-10:
            objects.append(
                segment(
                    f"Inspection/reference-error-{index}", expected, measured, (1, 0.6, 0.2), 0.002
                )
            )
    return EvidenceGeometry(
        title="Independent reference errors",
        scope="Surveyed references in teal; reconstructed points in amber; errors at actual length (1:1). Reference positions were not computed from the candidate. Empty geometry means no accepted reference measurements.",
        objects=tuple(objects),
        viewing_cameras=frame_evidence(objects),
        numbers={
            "report_id": identity,
            "references": [row.model_dump(mode="json") for row in references],
        },
    )


def target_geometry(target: TargetPose, identity: str) -> EvidenceGeometry:
    tcp = np.array(target.tcp_target.matrix)
    flange = np.array(target.flange_target.matrix)
    approach = np.array(target.approach_tcp.matrix)
    objects = axes("Inspection/target-TCP", tcp, 0.07) + axes(
        "Inspection/target-flange", flange, 0.06
    )
    objects += axes("Inspection/approach-TCP", approach, 0.04)
    objects.append(
        segment("Inspection/approach", approach[:3, 3], tcp[:3, 3], (1, 0.8, 0.2), 0.004)
    )
    return EvidenceGeometry(
        title="Saved grasp, approach and command target",
        scope="Python-computed saved target; XYZ axes show orientation, yellow line shows approach. This planned target is not proof of execution and inspection cannot dispatch it.",
        objects=tuple(objects),
        numbers={"record_id": identity, **target.model_dump(mode="json")},
    )
