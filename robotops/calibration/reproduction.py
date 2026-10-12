"""Offline recomputation from hashed saved pixels; never activates or executes anything."""

import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np

from robotops.calibration.acquisition import AcquisitionReport, CapturePlan, assess
from robotops.calibration.agreement import CameraAgreement, compare_cameras
from robotops.calibration.checks import RoutineCheck, evaluate_references
from robotops.calibration.contracts import (
    ArtifactRef,
    Board,
    Calculation,
    CalibrationArtifact,
    Camera,
    Candidate,
    Capture,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PointMeasurement,
    PoseSample,
    ReferenceBatch,
    SurfaceDetection,
    Tool,
    Transform,
    ValidationReport,
)
from robotops.calibration.depth import pixel_to_base, reconstruct
from robotops.calibration.diagnostics import InvestigationInputs, InvestigationReport, investigate
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import estimate_board, fit
from robotops.calibration.geometry import from_xyzw, residual
from robotops.calibration.measurement_quality import assess_measurement
from robotops.calibration.optics import CameraModelReport, OpticalReference, verify_camera_model
from robotops.calibration.outcome import PickOutcome, summarize_pick
from robotops.calibration.perception import red_cube_top, reference_center
from robotops.calibration.presentation import CapturePresentation, capture_geometry
from robotops.calibration.provenance import source_fingerprints, source_snapshot
from robotops.calibration.runtime_contracts import SensorSnapshot
from robotops.calibration.tcp import (
    GraspSpecification,
    ToolMeasurements,
    ToolVerification,
    construct_target,
    verify_measurements,
)
from robotops.calibration.validation import validate
from robotops.cell.calibration_motion import ControllerFrame
from robotops.domain.models import CommandReceipt, RobotCommand
from robotops.workflow.store import digest


def _check_corners(actual: PoseSample, saved: PoseSample) -> None:
    if (
        actual.corner_ids != saved.corner_ids
        or actual.excluded_corner_ids != saved.excluded_corner_ids
        or not np.allclose(actual.image_points_px, saved.image_points_px, atol=1e-7, rtol=0)
        or (
            saved.excluded_image_points_px is not None
            and (
                actual.excluded_image_points_px is None
                or not np.allclose(
                    actual.excluded_image_points_px,
                    saved.excluded_image_points_px,
                    atol=1e-7,
                    rtol=0,
                )
            )
        )
    ):
        raise CalibrationError("RECOMPUTED_CORNERS_DIFFER", saved.capture_id)


def reproduce(bundle: Path) -> dict[str, object]:
    """Verify byte hashes and recompute saved scientific stages using shared modules.

    Current repository code is used; archived source is compared, never executed.
    A differing source identity is explicitly not an exact-source reproduction pass.
    No files, approvals, lifecycle states or controller commands are written here.
    """
    archive = ZipFile(bundle) if bundle.is_file() else None
    try:

        def read(path: str) -> bytes:
            if archive is not None:
                entry = archive.getinfo(path)
                if entry.file_size > 64 * 1024 * 1024:
                    raise CalibrationError("EVIDENCE_ENTRY_TOO_LARGE", path)
                return archive.read(entry)
            target = (bundle / path).resolve()
            if not target.is_relative_to(bundle.resolve()):
                raise CalibrationError("UNSAFE_ARTIFACT_PATH")
            return target.read_bytes()

        manifest = json.loads(read("manifest.json"))
        if manifest.get("format") != "robotops-calibration-evidence-1":
            raise CalibrationError("UNSUPPORTED_EVIDENCE_BUNDLE")
        records = {(item["kind"], item["id"]): item["body"] for item in manifest["records"]}
        if len(records) != len(manifest["records"]):
            raise CalibrationError("DUPLICATE_EVIDENCE_RECORD")
        for item in manifest["records"]:
            canonical = json.dumps(item["body"], sort_keys=True, separators=(",", ":")).encode()
            if hashlib.sha256(canonical).hexdigest() != item["sha256"]:
                raise CalibrationError("EVIDENCE_RECORD_HASH_MISMATCH", item["id"])
        blobs: dict[str, bytes] = {}
        captures = {
            identity: Capture.model_validate(body)
            for (kind, identity), body in records.items()
            if kind == "capture"
        }
        surfaces = {
            identity: SurfaceDetection.model_validate(body)
            for (kind, identity), body in records.items()
            if kind == "surface-detection"
        }
        blob_refs = [ref for capture in captures.values() for ref in (capture.rgb, capture.depth)]
        blob_refs.extend(surface.mask for surface in surfaces.values())
        for reference in blob_refs:
            if reference.path not in blobs:
                data = read("images/" + reference.path)
                if hashlib.sha256(data).hexdigest() != reference.sha256:
                    raise CalibrationError("ARTIFACT_HASH_MISMATCH", reference.path)
                blobs[reference.path] = data

        def rgb(reference: ArtifactRef) -> np.ndarray:
            image = cv2.imdecode(
                np.frombuffer(blobs[reference.path], dtype=np.uint8), cv2.IMREAD_COLOR
            )
            if image is None or tuple(image.shape) != reference.shape:
                raise CalibrationError("RGB_ARTIFACT_SHAPE")
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        depths = {}
        for capture in captures.values():
            depth = np.load(io.BytesIO(blobs[capture.depth.path]), allow_pickle=False)
            if depth.dtype != np.float32 or tuple(depth.shape) != capture.depth.shape:
                raise CalibrationError("DEPTH_ARTIFACT_SHAPE")
            depths[capture.capture_id] = depth
        current_sources = source_fingerprints()
        results = []
        for (kind, _), body in records.items():
            if kind != "candidate":
                continue
            saved = Candidate.model_validate(body)
            lineage_matches = True
            if saved.reused_from is not None:
                parent = CalibrationArtifact.model_validate(
                    records[("artifact", saved.reused_from.artifact_id)]
                )
                lineage_matches = (
                    saved.reused_from.artifact_fingerprint == parent.fingerprint()
                    and saved.reused_from.candidate_fingerprint == parent.candidate.fingerprint()
                    and saved.model_dump(exclude={"candidate_id", "reused_from"})
                    == parent.candidate.model_dump(exclude={"candidate_id", "reused_from"})
                )
            limits = Limits.model_validate(records[("limits", saved.limits_fingerprint)])
            samples = []
            input_sample_ids = (
                tuple(row.sample_id for row in saved.fit_diagnostics.residuals)
                if saved.fit_diagnostics
                else saved.sample_ids
            )
            for sample_id in input_sample_ids:
                capture = captures[sample_id]
                sample = estimate_board(
                    capture, rgb(capture.rgb), saved.camera, saved.board, limits
                )
                old_sample = PoseSample.model_validate(records[("sample", sample_id)])
                _check_corners(sample, old_sample)
                samples.append(sample)
            fit_arguments = (
                {"policy": saved.fit_diagnostics.policy} if saved.fit_diagnostics else {}
            )
            fitted = fit(
                samples,
                saved.camera,
                saved.board,
                limits,
                saved.candidate_id,
                saved.y if saved.mounting_known else None,
                **fit_arguments,
            )
            x = residual(np.array(saved.x.matrix), np.array(fitted.x.matrix))
            y = residual(np.array(saved.y.matrix), np.array(fitted.y.matrix))
            different_sources = [
                path
                for path, digest in saved.source_fingerprints.items()
                if current_sources.get(path) != digest
            ]
            results.append(
                {
                    "candidate_id": saved.candidate_id,
                    "camera_id": saved.camera.camera_id,
                    "accepted_images_reprocessed": len(saved.sample_ids),
                    "input_images_reprocessed": len(samples),
                    "x_difference_m_rad": x,
                    "y_difference_m_rad": y,
                    "numerical_match": max(*x, *y) < 1e-7
                    and fitted.excluded_sample_ids == saved.excluded_sample_ids
                    and lineage_matches,
                    "saved_estimate_lineage_matches": lineage_matches,
                    "reused_from_artifact": saved.reused_from.artifact_id
                    if saved.reused_from
                    else None,
                    "excluded_fit_samples": list(fitted.excluded_sample_ids),
                    "different_source_paths": different_sources,
                }
            )
        validations, runtime_points, targets, tools, optics, acquisitions = [], [], [], [], [], []
        surface_results, reference_results, batch_results, agreement_results, routine_results = (
            [],
            [],
            [],
            [],
            [],
        )
        measurement_quality_results = []
        investigation_results = []
        pick_outcome_results = []
        application_records = {
            (item["kind"], item["id"]): item["body"] for item in manifest["application_records"]
        }
        for (kind, identity), body in records.items():
            if kind == "surface-detection":
                surface = surfaces[identity]
                capture = captures[identity]
                identify = (
                    reference_center if surface.method == "reference_center" else red_cube_top
                )
                pixel, mask = identify(rgb(capture.rgb))
                saved_mask = np.load(io.BytesIO(blobs[surface.mask.path]), allow_pickle=False)
                surface_results.append(
                    {
                        "capture_id": identity,
                        "method": surface.method,
                        "matches_saved": surface.camera_id == capture.camera_id
                        and tuple(saved_mask.shape) == surface.mask.shape
                        and saved_mask.dtype == np.bool_
                        and np.array_equal(mask, saved_mask)
                        and pixel == surface.selected_rgb_pixel
                        and int(mask.sum()) == surface.selected_pixel_count,
                    }
                )
            elif kind == "investigation":
                investigation = InvestigationReport.model_validate(body)
                inputs = InvestigationInputs.model_validate(
                    records[("investigation-input", identity)]
                )
                original_source = records[(inputs.source_kind, inputs.source_id)]
                source_fingerprint = hashlib.sha256(
                    json.dumps(original_source, sort_keys=True, separators=(",", ":")).encode()
                ).hexdigest()
                investigation_results.append(
                    {
                        "investigation_id": identity,
                        "matches_saved": investigate(identity, inputs) == investigation
                        and source_fingerprint == inputs.source_fingerprint,
                    }
                )
            elif kind == "pick-outcome":
                outcome = PickOutcome.model_validate(body)
                calculated = summarize_pick(
                    outcome.command, outcome.receipt, outcome.observation, outcome.verification
                )
                matching = calculated == outcome
                for model, record_id in (
                    (outcome.command, outcome.command.command_id),
                    (outcome.observation, outcome.observation.observation_id),
                    (outcome.verification, outcome.verification.verification_id),
                ):
                    matching &= application_records.get(
                        (type(model).__name__, record_id)
                    ) == model.model_dump(mode="json")
                pick_outcome_results.append({"outcome_id": identity, "matches_saved": matching})
            elif kind == "reference-batch":
                batch = ReferenceBatch.model_validate(body)
                matches = all(
                    captures.get(item.capture.capture_id) == item.capture for item in batch.captures
                )
                for item in batch.captures:
                    saved_reference_body = records.get(("reference", item.reference_id))
                    if saved_reference_body is not None:
                        matches &= (
                            IndependentReference.model_validate(saved_reference_body).base_point_m
                            == item.base_point_m
                        )
                batch_results.append(
                    {
                        "batch_id": identity,
                        "matches_saved": matches,
                        "capture_count": len(batch.captures),
                        "scope": "Audit independent survey bindings; no sensor recapture",
                    }
                )
            elif kind == "runtime-acquisition":
                snapshot = SensorSnapshot.model_validate(body)
                batch_results.append(
                    {
                        "batch_id": identity,
                        "matches_saved": all(
                            captures.get(item.capture_id) == item for item in snapshot.captures
                        ),
                        "capture_count": len(snapshot.captures),
                        "scope": "Saved sensor snapshot audit, not new acquisition",
                    }
                )
            elif kind == "routine-check":
                check = RoutineCheck.model_validate(body)
                artifact = CalibrationArtifact.model_validate(
                    records[("artifact", check.artifact_id)]
                )
                calls = [
                    trace
                    for (trace_kind, _), trace in records.items()
                    if trace_kind == "calculation-trace"
                    and trace.get("output", {})
                    and trace["output"].get("check_id") == check.check_id
                ]
                if not calls:
                    raise CalibrationError("ROUTINE_CHECK_CALL_INPUTS_MISSING", identity)
                limits = Limits.model_validate(calls[-1]["inputs"]["limits"])
                refs = []
                for row in check.references:
                    saved_routine_reference = IndependentReference.model_validate(
                        records[("reference", row.reference_id)]
                    )
                    capture = captures[row.reference_id]
                    pixel, mask = reference_center(rgb(capture.rgb))
                    measurement = reconstruct(
                        pixel,
                        depths[capture.capture_id],
                        artifact.candidate.camera,
                        artifact.candidate.x,
                        limits,
                        rgb_surface_mask=mask,
                    )
                    refs.append(
                        saved_routine_reference.model_copy(update={"measurement": measurement})
                    )
                rejected_match = True
                for capture_id in check.failed_capture_ids:
                    capture = captures[capture_id]
                    try:
                        pixel, mask = reference_center(rgb(capture.rgb))
                        reconstruct(
                            pixel,
                            depths[capture_id],
                            artifact.candidate.camera,
                            artifact.candidate.x,
                            limits,
                            rgb_surface_mask=mask,
                        )
                    except CalibrationError as error:
                        rejected_match &= error.code == records[("rejection", capture_id)]["reason"]
                    else:
                        rejected_match = False
                checked = evaluate_references(
                    identity,
                    check.camera_id,
                    check.artifact_id,
                    tuple(refs),
                    check.failed_capture_ids,
                    limits,
                )
                routine_results.append(
                    {
                        "check_id": identity,
                        "matches_saved": checked == check and rejected_match,
                        "rejections_rechecked": len(check.failed_capture_ids),
                    }
                )
            elif kind == "camera-model-report":
                saved_optics = CameraModelReport.model_validate(body)
                camera = Camera.model_validate(
                    records[("camera", saved_optics.camera_configuration_fingerprint)]
                )
                optical_references = tuple(
                    OpticalReference.model_validate(
                        records[("optical-reference", item.measurement_id)]
                    )
                    for item in saved_optics.streams
                )
                recomputed_optics = verify_camera_model(
                    camera, optical_references, saved_optics.limits, saved_optics.report_id
                )
                optics.append(
                    {"report_id": identity, "matches_saved": recomputed_optics == saved_optics}
                )
            elif kind == "acquisition-report":
                saved_acquisition = AcquisitionReport.model_validate(body)
                plan = CapturePlan.model_validate(
                    records[("capture-plan", saved_acquisition.plan_id)]
                )
                camera = Camera.model_validate(records[("camera", plan.camera_fingerprint)])
                board = Board.model_validate(records[("board", plan.board_fingerprint)])
                limits = Limits.model_validate(
                    records[("limits", saved_acquisition.limits_fingerprint)]
                )
                selected_captures = sorted(
                    (
                        capture
                        for capture in captures.values()
                        if capture.camera_id == plan.camera_id
                        and capture.dataset_id == plan.dataset_id
                    ),
                    key=lambda item: item.capture_id,
                )
                accepted, rejections = [], []
                for capture in selected_captures:
                    try:
                        detected = estimate_board(capture, rgb(capture.rgb), camera, board, limits)
                    except CalibrationError as error:
                        rejections.append(
                            MeasurementRejection(
                                capture_id=capture.capture_id,
                                reason=error.code,
                                detail=error.detail,
                                calculation=Calculation.model_validate(error.calculation)
                                if error.calculation
                                else None,
                                stage="board_pose" if capture.admitted else "acquisition",
                            )
                        )
                    else:
                        _check_corners(
                            detected,
                            PoseSample.model_validate(records[("sample", capture.capture_id)]),
                        )
                        accepted.append(detected)
                recalculated_acquisition = assess(
                    plan, selected_captures, accepted, rejections, camera, limits
                )
                acquisitions.append(
                    {
                        "report_id": identity,
                        "matches_saved": recalculated_acquisition == saved_acquisition,
                        "accepted_count": len(accepted),
                        "rejected_count": len(rejections),
                        "ready_to_fit": recalculated_acquisition.ready_to_fit,
                    }
                )
            elif kind == "validation":
                saved_report = ValidationReport.model_validate(body)
                candidate = Candidate.model_validate(
                    records[("candidate", saved_report.candidate_id)]
                )
                limits = Limits.model_validate(records[("limits", saved_report.limits_fingerprint)])
                held_out = [
                    estimate_board(
                        captures[row.capture_id],
                        rgb(captures[row.capture_id].rgb),
                        candidate.camera,
                        candidate.board,
                        limits,
                    )
                    for row in saved_report.images
                ]
                for sample in held_out:
                    _check_corners(
                        sample, PoseSample.model_validate(records[("sample", sample.capture_id)])
                    )
                references = []
                for row in saved_report.references:
                    saved_reference = IndependentReference.model_validate(
                        records[("reference", row.reference_id)]
                    )
                    capture = captures[row.reference_id]
                    pixel, mask = reference_center(rgb(capture.rgb))
                    measurement = reconstruct(
                        pixel,
                        depths[capture.capture_id],
                        candidate.camera,
                        candidate.x,
                        limits,
                        rgb_surface_mask=mask,
                    )
                    references.append(
                        saved_reference.model_copy(update={"measurement": measurement})
                    )
                recalculated = validate(
                    candidate,
                    held_out,
                    references,
                    limits,
                    identity,
                    saved_report.rejected_measurements,
                )
                rejected_match = True
                for rejected in saved_report.rejected_measurements:
                    capture = captures[rejected.capture_id]
                    try:
                        if rejected.stage == "depth":
                            pixel, mask = reference_center(rgb(capture.rgb))
                            reconstruct(
                                pixel,
                                depths[capture.capture_id],
                                candidate.camera,
                                candidate.x,
                                limits,
                                rgb_surface_mask=mask,
                            )
                        else:
                            estimate_board(
                                capture, rgb(capture.rgb), candidate.camera, candidate.board, limits
                            )
                    except CalibrationError as error:
                        rejected_match &= error.code == rejected.reason
                        if rejected.calculation is not None:
                            rejected_match &= error.calculation == rejected.calculation.model_dump(
                                mode="json"
                            )
                    else:
                        rejected_match = False
                validations.append(
                    {
                        "report_id": identity,
                        "matches_saved": recalculated == saved_report and rejected_match,
                        "rejections_rechecked": len(saved_report.rejected_measurements),
                        "image_count": len(held_out),
                        "reference_count": len(references),
                        "passed_validation": recalculated.passed,
                    }
                )
            elif kind == "tool-measurements":
                measurements = ToolMeasurements.model_validate(body)
                saved_check = ToolVerification.model_validate(
                    records[("tool-verification", identity)]
                )
                tools.append(
                    {
                        "measurement_id": identity,
                        "matches_saved": verify_measurements(measurements) == saved_check,
                    }
                )
            elif kind == "calculation-trace" and body.get("output") is not None:
                inputs = body["inputs"]
                if (
                    body["path"] == "robotops/calibration/depth.py"
                    and body["symbol"] == "reconstruct"
                ):
                    capture = captures[inputs["capture_id"]]
                    pixel, mask = reference_center(rgb(capture.rgb))
                    reference_point = reconstruct(
                        pixel,
                        depths[capture.capture_id],
                        Camera.model_validate(inputs["camera"]),
                        Transform.model_validate(inputs["x"]),
                        Limits.model_validate(inputs["limits"]),
                        rgb_surface_mask=mask,
                    )
                    surface = surfaces[capture.capture_id]
                    reference_results.append(
                        {
                            "capture_id": capture.capture_id,
                            "trace_id": identity,
                            "matches_saved": reference_point.model_dump(mode="json")
                            == body["output"]
                            and list(pixel) == inputs["selected_rgb_pixel"]
                            and capture.depth.model_dump(mode="json") == inputs["depth"]
                            and surface.mask.model_dump(mode="json") == inputs["rgb_surface_mask"],
                        }
                    )
                elif (
                    body["path"] == "robotops/calibration/measurement_quality.py"
                    and body["symbol"] == "assess_measurement"
                ):
                    quality_report = assess_measurement(
                        PointMeasurement.model_validate(inputs["point"]),
                        SurfaceDetection.model_validate(inputs["detection"]),
                        CameraAgreement.model_validate(inputs["agreement"]),
                        CalibrationArtifact.model_validate(
                            records[("artifact", inputs["artifact_id"])]
                        ),
                        Limits.model_validate(inputs["limits"]),
                    )
                    measurement_quality_results.append(
                        {
                            "quality_id": quality_report.quality_id,
                            "matches_saved": quality_report.model_dump(mode="json")
                            == body["output"]
                            and body["output"]
                            == records[("measurement-quality", quality_report.quality_id)],
                        }
                    )
                elif (
                    body["path"] == "robotops/calibration/agreement.py"
                    and body["symbol"] == "compare_cameras"
                ):
                    agreement = compare_cameras(
                        body["output"]["agreement_id"],
                        PointMeasurement.model_validate(inputs["primary"]),
                        PointMeasurement.model_validate(inputs["secondary"]),
                        CalibrationArtifact.model_validate(
                            records[("artifact", inputs["first_artifact_id"])]
                        ),
                        CalibrationArtifact.model_validate(
                            records[("artifact", inputs["second_artifact_id"])]
                        ),
                        Limits.model_validate(inputs["first_limits"]),
                        Limits.model_validate(inputs["second_limits"]),
                    )
                    agreement_results.append(
                        {
                            "trace_id": identity,
                            "matches_saved": agreement.model_dump(mode="json") == body["output"],
                        }
                    )
                elif (
                    body["path"] == "robotops/calibration/depth.py"
                    and body["symbol"] == "pixel_to_base"
                ):
                    artifact = CalibrationArtifact.model_validate(
                        records[("artifact", inputs["artifact_id"])]
                    )
                    capture = captures[inputs["capture_id"]]
                    pixel, mask = red_cube_top(rgb(capture.rgb))
                    result = pixel_to_base(
                        pixel,
                        depths[capture.capture_id],
                        artifact.candidate.camera,
                        artifact,
                        Limits.model_validate(inputs["limits"]),
                        active_valid=True,
                        rgb_surface_mask=mask,
                    )
                    runtime_points.append(
                        {
                            "capture_id": capture.capture_id,
                            "matches_saved": result.model_dump(mode="json") == body["output"],
                            "scope": "Historical approved artifact recomputation; does not establish current applicability",
                        }
                    )
                elif (
                    body["path"] == "robotops/calibration/tcp.py"
                    and body["symbol"] == "construct_target"
                ):
                    target = construct_target(
                        PointMeasurement.model_validate(inputs["point"]),
                        GraspSpecification.model_validate(inputs["grasp"]),
                        Tool.model_validate(inputs["tool"]),
                        ToolVerification.model_validate(inputs["verification"]),
                        inputs["command_mode"],
                    )
                    targets.append(
                        {
                            "record_id": inputs["record_id"],
                            "trace_id": identity,
                            "matches_saved": target.model_dump(mode="json") == body["output"],
                        }
                    )
        controller_results = []
        capture_presentations = []
        controller = manifest.get("controller")
        if controller is not None:
            canonical_controller = json.dumps(
                {key: value for key, value in controller.items() if key != "sha256"},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            if hashlib.sha256(canonical_controller).hexdigest() != controller.get("sha256"):
                raise CalibrationError("CONTROLLER_EVIDENCE_HASH_MISMATCH")
            for body in controller.get("capture_presentations", []):
                saved_scene = CapturePresentation.model_validate(body)
                presented_capture = captures.get(saved_scene.capture_id)
                matching = False
                if presented_capture is not None:
                    capture_geometry(saved_scene, presented_capture)
                    flange = next(
                        (
                            item
                            for item in saved_scene.scene.objects
                            if item.name == "Robot/ToolChanger"
                        ),
                        None,
                    )
                    if flange and flange.quaternion_xyzw is not None:
                        matching = np.allclose(
                            from_xyzw(flange.position, flange.quaternion_xyzw),
                            presented_capture.t_b_f.matrix,
                            atol=1e-10,
                            rtol=0,
                        )
                capture_presentations.append(
                    {
                        "capture_id": saved_scene.capture_id,
                        "matches_saved": bool(matching),
                        "scope": "Reported flange agrees with saved presentation; physical layout is labelled instructor data, not a fitted result",
                    }
                )
            application_commands = {
                item["id"]: RobotCommand.model_validate(item["body"])
                for item in manifest["application_records"]
                if item["kind"] == "RobotCommand"
            }
            for item in controller["commands"]:
                command = RobotCommand.model_validate(item["command"])
                receipt = CommandReceipt.model_validate(item["receipt"])
                frames = [
                    ControllerFrame.model_validate(frame)
                    for frame in controller["motion_frames"]
                    if frame["command_id"] == command.command_id
                ]
                matching = (
                    command == application_commands.get(command.command_id)
                    and digest(command) == item["payload_hash"]
                )
                matching &= (
                    receipt.command_id == command.command_id
                    and receipt.payload_hash == item["payload_hash"]
                )
                missed_transfer = bool(
                    receipt.calibrated_receipt
                    and receipt.calibrated_receipt.motion_without_transfer
                )
                if command.calibrated_plan is not None and (
                    receipt.effect_count == 1 or missed_transfer
                ):
                    matching &= len(frames) == 121 and [frame.index for frame in frames] == list(
                        range(121)
                    )
                    if frames:
                        for waypoint in command.calibrated_plan.waypoints:
                            frame = min(
                                frames, key=lambda item: abs(item.sim_time_s - waypoint.sim_time_s)
                            )
                            matching &= np.allclose(
                                frame.machine.flange.matrix,
                                waypoint.flange.matrix,
                                atol=1e-9,
                                rtol=0,
                            )
                            matching &= np.allclose(
                                frame.machine.tcp.matrix, waypoint.tcp.matrix, atol=1e-9, rtol=0
                            )
                        if missed_transfer:
                            matching &= all(
                                not frame.attached and frame.object_pose == frames[0].object_pose
                                for frame in frames
                            )
                elif command.calibrated_plan is not None:
                    matching &= not frames
                controller_results.append(
                    {
                        "command_id": command.command_id,
                        "matches_saved": bool(matching),
                        "effect_count": receipt.effect_count,
                        "controller_frame_count": len(frames),
                    }
                )
        # Also bind datasets that never produced a candidate (e.g. rejected timing
        # acquisitions) to the exact displayed source of their recorded calls.
        trace_source_differences = []
        for (kind, identity), body in records.items():
            if kind == "calculation-trace":
                current = source_snapshot(body["path"], body["symbol"])
                if current["displayed_sha256"] != body["source"]["displayed_sha256"]:
                    trace_source_differences.append(identity)
        stages = (
            validations
            + runtime_points
            + targets
            + tools
            + optics
            + acquisitions
            + controller_results
            + capture_presentations
            + surface_results
            + reference_results
            + batch_results
            + agreement_results
            + routine_results
            + measurement_quality_results
            + investigation_results
            + pick_outcome_results
        )
        return {
            "scope": "Read-only image fitting, independent validation, depth, TCP/target recomputation and controller-record audit; never re-approves or executes",
            "run_id": manifest["run_id"],
            "seed": manifest["seed"],
            "verified_artifact_count": len(blobs),
            "results": results,
            "validation_results": validations,
            "runtime_point_results": runtime_points,
            "target_results": targets,
            "tool_results": tools,
            "controller_results": controller_results,
            "capture_presentation_results": capture_presentations,
            "optical_model_results": optics,
            "acquisition_results": acquisitions,
            "surface_detection_results": surface_results,
            "reference_calculation_results": reference_results,
            "capture_batch_results": batch_results,
            "camera_agreement_results": agreement_results,
            "routine_check_results": routine_results,
            "measurement_quality_results": measurement_quality_results,
            "investigation_results": investigation_results,
            "pick_outcome_results": pick_outcome_results,
            "different_trace_source_ids": trace_source_differences,
            "limits": [
                "Controller records are audited, not a second physical execution.",
                "Validation rejections are rechecked against their raw captures and saved reason codes.",
                "Older bundles without controller telemetry retain their narrower reproduction scope.",
            ],
            "passed": bool(results or acquisitions)
            and not trace_source_differences
            and all(
                item["numerical_match"] and not item["different_source_paths"] for item in results
            )
            and all(item["matches_saved"] for item in stages),
        }
    finally:
        if archive is not None:
            archive.close()
