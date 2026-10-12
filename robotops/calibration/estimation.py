"""Measured calibration: images/robot reports in; inactive estimates out.

No dependency on simulator/oracle/physical-state modules is permitted here. The
public camera model supplies intrinsics; it does not supply camera extrinsics.
"""

import platform
from collections.abc import Sequence
from typing import Literal, cast

import cv2
import numpy as np
from numpy.typing import NDArray
from scipy.spatial.transform import Rotation

from robotops.calibration.configuration import charuco_board, framed
from robotops.calibration.contracts import (
    Board,
    Calculation,
    Camera,
    Candidate,
    Capture,
    Coverage,
    FitDiagnostics,
    FitResidual,
    Limits,
    PoseConditioning,
    PoseSample,
    RobustFitPolicy,
    Transform,
    Vec2,
    Vec3,
)
from robotops.calibration.errors import CalibrationError
from robotops.calibration.geometry import (
    Array,
    inverse,
    point_rms,
    points,
    project,
    residual,
    rigid_mean,
    transform,
    undistort,
)
from robotops.calibration.provenance import source_fingerprints


def _camera_projection(camera: Camera, coordinates: Array) -> Array:
    return project(
        coordinates,
        np.asarray(camera.rgb.k),
        np.asarray(camera.rgb.coefficients),
        camera.rgb.distortion_model,
    )


def pose_conditioning(
    pose: Array, objects: Array, camera: Camera, image_rms_px: float, limits: Limits
) -> PoseConditioning:
    """Image-only local observability gate, before seeing X or any holdout residual.

    Central differences perturb rotation in radians and translation in meters.
    Propagate isotropic image uncertainty through the model-correct projection.
    A fixed 0.2 px noise floor prevents perfect-fit small point sets claiming certainty.
    Require three-sigma sensitivity to fit within the existing separate chain budgets.
    This is not a posterior probability of correctness; systematic errors remain.
    """

    def projected(delta: Array) -> Array:
        changed = pose.copy()
        changed[:3, :3] = Rotation.from_rotvec(delta[:3]).as_matrix() @ pose[:3, :3]
        changed[:3, 3] += delta[3:]
        return _camera_projection(camera, points(changed, objects)).ravel()

    epsilon = 1e-6
    jacobian = np.column_stack(
        [
            (projected(axis * epsilon) - projected(-axis * epsilon)) / (2 * epsilon)
            for axis in np.eye(6)
        ]
    )
    if np.linalg.matrix_rank(jacobian) != 6:
        raise CalibrationError(
            "PNP_POSE_UNDERCONSTRAINED",
            "Projection Jacobian has fewer than six independent directions",
        )
    sigma = max(0.2, image_rms_px / np.sqrt(2))
    covariance = np.linalg.inv(jacobian.T @ jacobian) * sigma**2
    report = PoseConditioning(
        pixel_sigma=float(sigma),
        translation_sigma_mm=float(
            np.sqrt(max(0, np.linalg.eigvalsh(covariance[3:, 3:])[-1])) * 1000
        ),
        rotation_sigma_deg=float(
            np.rad2deg(np.sqrt(max(0, np.linalg.eigvalsh(covariance[:3, :3])[-1])))
        ),
    )
    if (
        limits.max_chain_translation_mm is None
        or limits.max_chain_rotation_deg is None
        or 3 * report.translation_sigma_mm > limits.max_chain_translation_mm
        or 3 * report.rotation_sigma_deg > limits.max_chain_rotation_deg
    ):
        raise CalibrationError("PNP_POSE_UNDERCONSTRAINED", report.model_dump_json())
    return report


def estimate_board(
    capture: Capture, rgb: NDArray[np.uint8], camera: Camera, board: Board, limits: Limits
) -> PoseSample:
    """Detect actual ChArUco pixels; retain IDs, IPPE choices, LM result and exclusions."""
    if capture.camera_id != camera.camera_id or capture.profile_id != camera.profile_id:
        raise CalibrationError("CAMERA_PROFILE_MISMATCH")
    if capture.configuration_fingerprint != camera.fingerprint():
        raise CalibrationError("CAMERA_CONFIGURATION_CHANGED")
    if capture.board_fingerprint != board.fingerprint():
        raise CalibrationError("BOARD_CONFIGURATION_CHANGED")
    if not capture.admitted or not capture.settled or capture.moving:
        raise CalibrationError("ACQUISITION_REJECTED", ", ".join(capture.rejection_codes))
    timestamps = [capture.rgb_timestamp_s, capture.depth_timestamp_s, capture.robot_timestamp_s]
    if max(timestamps) - min(timestamps) > limits.max_timestamp_skew_s:
        raise CalibrationError("TIMESTAMP_MISMATCH")
    if capture.partition == "runtime":
        raise CalibrationError("WRONG_MEASUREMENT_PARTITION")
    if rgb.shape != (camera.rgb.height, camera.rgb.width, 3) or rgb.dtype != np.uint8:
        raise CalibrationError("RGB_PROFILE_SHAPE_MISMATCH")
    definition = charuco_board(board)
    detector = cv2.aruco.CharucoDetector(definition)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    corners, identities, _, marker_ids = detector.detectBoard(gray)
    if marker_ids is not None:
        unexpected = set(int(value) for value in marker_ids.ravel()) - set(
            int(value) for value in definition.getIds()
        )
        if unexpected:
            raise CalibrationError(
                "MARKER_IDS_DO_NOT_MATCH_BOARD",
                f"Unexpected detected marker IDs: {sorted(unexpected)}",
            )
    if corners is None or identities is None or len(corners) < limits.min_corners:
        raise CalibrationError("INSUFFICIENT_DETECTED_CORNERS")
    # Refine measured checker intersections in the image, rather than treating marker
    # homography interpolation as final subpixel evidence. A small 3 px window avoids
    # the neighboring ArUco pattern; it is fixed before final holdout evaluation.
    cv2.cornerSubPix(
        gray,
        corners,
        (3, 3),
        (-1, -1),
        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 100, 0.001),
    )
    return estimate_correspondences(
        capture,
        np.asarray(corners, dtype=np.float64).reshape(-1, 2),
        np.asarray(identities, dtype=np.int32).ravel(),
        camera,
        board,
        limits,
    )


def estimate_correspondences(
    capture: Capture,
    image_points: Array,
    corner_ids: NDArray[np.int32],
    camera: Camera,
    board: Board,
    limits: Limits,
) -> PoseSample:
    """Shared PnP stage. Explicit observations also support analytical unit fixtures.

    Camera-model undistortion happens before planar robust rejection, IPPE and LM.
    No pinhole approximation is applied to fisheye measurements.
    """
    ids = [int(v) for v in corner_ids]
    if len(set(ids)) != len(ids) or any(v not in board.corner_ids for v in ids):
        raise CalibrationError("WRONG_OR_DUPLICATE_CORNER_IDS")
    pixels = np.asarray(image_points, dtype=np.float64)
    if pixels.shape != (len(ids), 2) or len(ids) < limits.min_corners:
        raise CalibrationError("INSUFFICIENT_CORRESPONDENCES")
    objects = np.asarray([board.corners_m[v] for v in ids])
    normalized = undistort(
        pixels,
        np.asarray(camera.rgb.k),
        np.asarray(camera.rgb.coefficients),
        camera.rgb.distortion_model,
    )
    if not np.isfinite(normalized).all():
        raise CalibrationError("UNDISTORTION_FAILED")
    # The homography is used only to reject gross corner outliers on this planar target.
    focal = min(camera.rgb.k[0][0], camera.rgb.k[1][1])
    _, mask = cv2.findHomography(
        objects[:, :2], normalized, cv2.RANSAC, limits.outlier_threshold_px / focal
    )
    if mask is None:
        raise CalibrationError("PLANAR_CORRESPONDENCE_FIT_FAILED")
    accepted = mask.ravel().astype(bool)
    excluded = tuple(v for v, keep in zip(ids, accepted, strict=True) if not keep)
    excluded_pixels = cast(tuple[Vec2, ...], tuple(map(tuple, pixels[~accepted].tolist())))
    if int(np.sum(accepted)) < limits.min_corners:
        raise CalibrationError("INSUFFICIENT_INLIER_CORNERS")
    objects, pixels, normalized = objects[accepted], pixels[accepted], normalized[accepted]
    accepted_ids = tuple(v for v, keep in zip(ids, accepted, strict=True) if keep)
    solution = cv2.solvePnPGeneric(
        objects, normalized, np.eye(3), np.zeros(4), flags=cv2.SOLVEPNP_IPPE
    )
    if not solution[0]:
        raise CalibrationError("PLANAR_PNP_FAILED")
    choices: list[tuple[float, Array, Array]] = []
    for rvec, tvec in zip(solution[1], solution[2], strict=True):
        rvec, tvec = cv2.solvePnPRefineLM(
            objects, normalized, np.eye(3), np.zeros(4), rvec.copy(), tvec.copy()
        )
        rotation, _ = cv2.Rodrigues(rvec)
        pose = transform(
            np.asarray(rotation, dtype=np.float64), np.asarray(tvec, dtype=np.float64).ravel()
        )
        coords = points(pose, objects)
        if (coords[:, 2] <= 0).any():
            continue
        errors = pixels - _camera_projection(camera, coords)
        score = point_rms(errors)
        # LM may converge both starts to the same minimum; that is not a second pose.
        if any(
            residual(pose, prior[1])[0] < 1e-5 and residual(pose, prior[1])[1] < 1e-4
            for prior in choices
        ):
            continue
        choices.append((score, pose, errors))
    if not choices:
        raise CalibrationError("NO_POSITIVE_DEPTH_POSE")
    choices.sort(key=lambda item: item[0])
    if len(choices) > 1 and choices[1][0] - choices[0][0] < limits.ambiguity_gap_px:
        raise CalibrationError(
            "UNRESOLVED_PLANAR_POSE_AMBIGUITY",
            f"Candidate point RMS: {[round(item[0], 6) for item in choices]} px",
            calculation=Calculation(
                function="robotops.calibration.estimation.estimate_correspondences",
                formula="IPPE -> LM on normalized undistorted points, K=I, D=0; reject distinct positive-depth poses when RMS_2-RMS_1 < ambiguity_gap_px",
                inputs={
                    "corner_ids": accepted_ids,
                    "image_points_px": pixels.tolist(),
                    "normalized_points": normalized.tolist(),
                    "object_points_t_m": objects.tolist(),
                    "t_b_f": capture.t_b_f.model_dump(mode="json"),
                    "camera": camera.model_dump(mode="json"),
                    "ambiguity_gap_px": limits.ambiguity_gap_px,
                },
                outputs={
                    "positive_depth_candidates": [
                        {
                            "rms_px": score,
                            "t_c_t": framed(pose, "t", "c").model_dump(mode="json"),
                            "residuals_px": errors.tolist(),
                        }
                        for score, pose, errors in choices
                    ],
                    "rms_gap_px": choices[1][0] - choices[0][0],
                },
                decision="REJECTED_UNRESOLVED_PLANAR_POSE_AMBIGUITY; no pose selected",
            ).model_dump(mode="json"),
        )
    score, pose, errors = choices[0]
    if limits.max_pnp_rms_px is None or score > limits.max_pnp_rms_px:
        raise CalibrationError("PNP_IMAGE_RESIDUAL_REJECTED", f"{score:.6f} px")
    conditioning = pose_conditioning(pose, objects, camera, score, limits)
    return PoseSample(
        capture_id=capture.capture_id,
        dataset_id=capture.dataset_id,
        camera_id=capture.camera_id,
        conditioning=conditioning,
        configuration_fingerprint=capture.configuration_fingerprint,
        board_fingerprint=capture.board_fingerprint,
        t_b_f=capture.t_b_f,
        t_c_t=framed(pose, "t", "c"),
        corner_ids=accepted_ids,
        object_points_m=cast(tuple[Vec3, ...], tuple(map(tuple, objects.tolist()))),
        image_points_px=cast(tuple[Vec2, ...], tuple(map(tuple, pixels.tolist()))),
        residuals_px=cast(tuple[Vec2, ...], tuple(map(tuple, errors.tolist()))),
        pnp_rms_px=score,
        excluded_corner_ids=excluded,
        excluded_image_points_px=excluded_pixels,
        candidate_rms_px=tuple(choice[0] for choice in choices),
        partition=cast(Literal["fit", "validation", "routine"], capture.partition),
    )


def coverage(samples: Sequence[PoseSample], camera: Camera, limits: Limits) -> Coverage:
    if not samples:
        return Coverage(
            sample_count=0,
            translation_span_m=(0, 0, 0),
            rotation_singular_values_rad=(0, 0, 0),
            image_fraction=0,
            failures=("INSUFFICIENT_SAMPLES",),
        )
    poses = np.asarray([s.t_b_f.matrix for s in samples])
    span = np.ptp(poses[:, :3, 3], axis=0)
    vectors = Rotation.from_matrix(poses[0, :3, :3].T @ poses[:, :3, :3]).as_rotvec()
    centered = vectors - np.mean(vectors, axis=0)
    singular = np.pad(
        np.linalg.svd(centered, compute_uv=False) / np.sqrt(len(samples)),
        (0, max(0, 3 - len(samples))),
    )
    pixels = np.concatenate([s.image_points_px for s in samples]).astype(np.float32)
    hull = cv2.convexHull(pixels)
    fraction = float(cv2.contourArea(hull) / (camera.rgb.width * camera.rgb.height))
    failures = []
    if len(samples) < limits.min_samples:
        failures.append("INSUFFICIENT_SAMPLES")
    if (span < np.asarray(limits.min_translation_span_m)).any():
        failures.append("INSUFFICIENT_POSITION_COVERAGE")
    # Two nonparallel rotation axes are necessary for hand-eye observability.
    if singular[1] < limits.min_rotation_singular_rad:
        failures.append("INSUFFICIENT_ROTATION_DIVERSITY")
    if fraction < limits.min_image_coverage:
        failures.append("INSUFFICIENT_IMAGE_COVERAGE")
    return Coverage(
        sample_count=len(samples),
        translation_span_m=cast(Vec3, tuple(span.tolist())),
        rotation_singular_values_rad=cast(Vec3, tuple(singular.tolist())),
        image_fraction=fraction,
        failures=tuple(failures),
    )


def _fit_transforms(
    a: Sequence[Array], b: Sequence[Array], weights: Sequence[float], known_mount: Transform | None
) -> tuple[Array, Array]:
    if known_mount is not None:
        if (known_mount.source, known_mount.destination) != ("t", "f"):
            raise CalibrationError("BOARD_MOUNT_FRAME_DIRECTION")
        y = np.asarray(known_mount.matrix)
    else:
        inverse_b = [inverse(value) for value in b]
        rotation, translation = cv2.calibrateHandEye(
            [value[:3, :3] for value in a],
            [value[:3, 3] for value in a],
            [value[:3, :3] for value in inverse_b],
            [value[:3, 3] for value in inverse_b],
            method=cv2.CALIB_HAND_EYE_PARK,
        )
        y = transform(
            np.asarray(rotation, dtype=np.float64),
            np.asarray(translation, dtype=np.float64).ravel(),
        )
    estimates = [ai @ y @ inverse(bi) for ai, bi in zip(a, b, strict=True)]
    return rigid_mean(estimates, weights), y


def fit(
    samples: Sequence[PoseSample],
    camera: Camera,
    board: Board,
    limits: Limits,
    candidate_id: str,
    known_mount: Transform | None = None,
    policy: RobustFitPolicy | None = None,
) -> Candidate:
    """Create an inactive candidate. Final-validation observations are prohibited inputs.

    Park-Martin mapping: A_i is gripper2base; inv(B_i) is target2cam; output is Y.
    The relation inv(A_j) A_i Y = Y inv(B_j) B_i is checked by independent tests.
    X_i=A_i Y inv(B_i); inverse pixel-variance weights use a 0.25 px noise floor.
    Reproducible training-only consensus rejects inconsistent robot/board pairs before
    the final rigid fit. It never inspects validation or uses mixed-unit thresholds.
    """
    policy = policy or RobustFitPolicy()
    if any(s.partition != "fit" for s in samples):
        raise CalibrationError("HOLDOUT_CANNOT_FIT_CANDIDATE")
    if len({s.capture_id for s in samples}) != len(samples):
        raise CalibrationError("DUPLICATE_FIT_SAMPLE")
    if known_mount is not None and (known_mount.source, known_mount.destination) != ("t", "f"):
        raise CalibrationError("BOARD_MOUNT_FRAME_DIRECTION")
    for sample in samples:
        if (
            sample.camera_id != camera.camera_id
            or sample.configuration_fingerprint != camera.fingerprint()
            or sample.board_fingerprint != board.fingerprint()
        ):
            raise CalibrationError("FIT_CONFIGURATION_MISMATCH")
        if sample.pnp_rms_px > (limits.max_pnp_rms_px or 0):
            raise CalibrationError("FIT_SAMPLE_QUALITY_REJECTED", sample.capture_id)
    measured_coverage = coverage(samples, camera, limits)
    if measured_coverage.failures:
        raise CalibrationError(
            "INSUFFICIENT_MEASUREMENT_QUALITY", ", ".join(measured_coverage.failures)
        )
    a = [np.asarray(s.t_b_f.matrix) for s in samples]
    b = [np.asarray(s.t_c_t.matrix) for s in samples]
    weights = [1.0 / max(0.25, sample.pnp_rms_px) ** 2 for sample in samples]
    if limits.max_chain_translation_mm is None or limits.max_chain_rotation_deg is None:
        raise CalibrationError("ROBUST_FIT_CHAIN_LIMITS_REQUIRED")
    translation_limit = limits.max_chain_translation_mm / 1000
    rotation_limit = float(np.deg2rad(limits.max_chain_rotation_deg))
    rng = np.random.default_rng(policy.seed)
    subsets = {tuple(range(len(samples)))}
    for _ in range(policy.hypothesis_count):
        subsets.add(
            tuple(
                sorted(
                    int(i)
                    for i in rng.choice(
                        len(samples), min(policy.subset_size, len(samples)), replace=False
                    )
                )
            )
        )
    best_indices: tuple[int, ...] = ()
    best_score = float("inf")
    valid_hypotheses = 0
    for indices in sorted(subsets):
        try:
            guess_x, guess_y = _fit_transforms(
                [a[i] for i in indices],
                [b[i] for i in indices],
                [weights[i] for i in indices],
                known_mount,
            )
        except (CalibrationError, cv2.error, np.linalg.LinAlgError):
            continue
        valid_hypotheses += 1
        errors = [residual(ai @ guess_y, guess_x @ bi) for ai, bi in zip(a, b, strict=True)]
        consensus = tuple(
            i
            for i, (distance, angle) in enumerate(errors)
            if distance <= translation_limit and angle <= rotation_limit
        )
        score = (
            float(
                np.median(
                    [
                        max(errors[i][0] / translation_limit, errors[i][1] / rotation_limit)
                        for i in consensus
                    ]
                )
            )
            if consensus
            else float("inf")
        )
        if (
            len(consensus) > len(best_indices)
            or len(consensus) == len(best_indices)
            and score < best_score
        ):
            best_indices, best_score = consensus, score
    if (
        len(best_indices) < limits.min_samples
        or len(best_indices) / len(samples) < 1 - policy.max_rejection_fraction
    ):
        raise CalibrationError(
            "NO_RELIABLE_TRAINING_CONSENSUS",
            f"{len(best_indices)}/{len(samples)} consistent observations; new measurements required",
        )
    retained = [samples[i] for i in best_indices]
    measured_coverage = coverage(retained, camera, limits)
    if measured_coverage.failures:
        raise CalibrationError(
            "RETAINED_CONSENSUS_COVERAGE_FAILED", ", ".join(measured_coverage.failures)
        )
    x, y = _fit_transforms(
        [a[i] for i in best_indices],
        [b[i] for i in best_indices],
        [weights[i] for i in best_indices],
        known_mount,
    )
    rows = []
    for i, (ai, bi) in enumerate(zip(a, b, strict=True)):
        distance, angle = residual(ai @ y, x @ bi)
        included = i in best_indices
        if included and (distance > translation_limit or angle > rotation_limit):
            raise CalibrationError("UNSTABLE_TRAINING_CONSENSUS", samples[i].capture_id)
        rows.append(
            FitResidual(
                sample_id=samples[i].capture_id,
                translation_mm=distance * 1000,
                rotation_deg=float(np.rad2deg(angle)),
                included=included,
                reason="RETAINED_TRAINING_CONSENSUS"
                if included
                else "EXCLUDED_INCONSISTENT_ROBOT_BOARD_PAIR",
            )
        )
    diagnostics = FitDiagnostics(
        policy=policy,
        tested_hypotheses=len(subsets),
        valid_hypotheses=valid_hypotheses,
        consensus_sample_ids=tuple(samples[i].capture_id for i in best_indices),
        residuals=tuple(rows),
    )
    return Candidate(
        candidate_id=candidate_id,
        camera=camera,
        board=board,
        x=framed(x, "c", "b"),
        y=framed(y, "t", "f"),
        mounting_known=known_mount is not None,
        sample_ids=tuple(s.capture_id for s in retained),
        excluded_sample_ids=tuple(row.sample_id for row in rows if not row.included),
        dataset_ids=tuple(sorted({s.dataset_id for s in samples})),
        coverage=measured_coverage,
        weights=tuple(weights[i] for i in best_indices),
        fit_diagnostics=diagnostics,
        solver="known-Y+SO3-chordal" if known_mount else "Park-Martin+SO3-chordal",
        software_version=f"Python {platform.python_version()}; OpenCV {cv2.__version__}",
        source_fingerprints=source_fingerprints(),
        limits_fingerprint=limits.fingerprint(),
    )
