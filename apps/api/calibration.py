"""Scoped calibration actions and read-only evidence over the existing world/session API."""

import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Literal, get_args
from uuid import uuid4

import cv2
import numpy as np
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response

from robotops.blender.visualization import VisualScene
from robotops.calibration.acquisition import (
    AcquisitionReport,
    CapturePlan,
    CaptureScenario,
    scenario_options,
)
from robotops.calibration.checks import RoutineCheck
from robotops.calibration.contracts import (
    CalibrationArtifact,
    Candidate,
    Capture,
    Id,
    Limits,
    PoseSample,
    Record,
    ValidationReport,
)
from robotops.calibration.diagnostics import InvestigationKind
from robotops.calibration.errors import CalibrationError
from robotops.calibration.faults import FaultKind, catalogue
from robotops.calibration.inspection import (
    DepthDisplay,
    depth_display,
    depth_preview,
    inspect_pixel,
)
from robotops.calibration.lifecycle import Mutation, OperationReceipt
from robotops.calibration.optics import CameraModelReport
from robotops.calibration.presentation import (
    EvidenceGeometry,
    capture_geometry,
    pose_geometry,
    reference_geometry,
    sample_geometry,
    target_geometry,
)
from robotops.calibration.provenance import source_snapshot
from robotops.calibration.service import CalibrationService
from robotops.calibration.tcp import TargetPose
from robotops.calibration.trace import ComputationTrace, result_record_keys
from robotops.workflow.engine import Engine
from robotops.workflow.store import NotFound


class InvestigationRequest(Mutation):
    kind: InvestigationKind
    identity: Id


class AcquireRequest(Mutation):
    dataset_id: Id
    repeated_poses: bool = False
    settled: bool = True
    timestamp_skew_s: float = 0
    scenario: CaptureScenario = "varied"


class FitRequest(Mutation):
    dataset_id: Id
    candidate_id: Id


class ValidationRequest(Mutation):
    dataset_id: Id
    candidate_id: Id


class ReuseRequest(Mutation):
    artifact_id: Id
    candidate_id: Id


class ApprovalRequest(Mutation):
    candidate_id: Id
    report_id: Id
    actor: str


class InvalidationRequest(Mutation):
    reason: str


class FaultRequest(Mutation):
    kind: FaultKind


class CameraMovementRequest(Mutation):
    translation_m: tuple[float, float, float] = (0.04, 0, 0)
    rotation_rad: tuple[float, float, float] = (0, 0.025, 0)


class HttpTrace(Record):
    trace_id: str
    run_id: str
    camera_id: str | None
    request_id: str | None
    started_at_utc: str
    finished_at_utc: str
    classification: Literal["HTTP"] = "HTTP"
    method: str
    path: str
    request_body: object
    response_status: int
    response_body: object
    scope: str = (
        "Actual local HTTP request and generated response; generation does not prove client receipt"
    )


RecordKind = Literal[
    "investigation",
    "pick-outcome",
    "capture-plan",
    "acquisition-report",
    "simulation-fault",
    "optical-reference",
    "camera-model-report",
    "capture",
    "sample",
    "candidate",
    "validation",
    "artifact",
    "reference",
    "reference-batch",
    "surface-detection",
    "measurement-quality",
    "runtime-acquisition",
    "rejection",
    "runtime-point",
    "runtime-point-error",
    "runtime-target",
    "observation-failure",
    "tool-measurements",
    "tool-verification",
    "validation-reservation",
    "calculation-trace",
    "http-trace",
    "camera-agreement",
    "routine-check",
]


def _mutation(request: Mutation) -> Mutation:
    return Mutation(request_id=request.request_id, expected_revision=request.expected_revision)


def mount_calibration_routes(app: FastAPI, workflow: Engine | None) -> None:
    @app.middleware("http")
    async def trace_transport(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if (
            request.method != "POST"
            or not request.url.path.startswith("/calibration/")
            or workflow is None
            or workflow.calibration is None
        ):
            return await call_next(request)
        started = datetime.now(UTC).isoformat()
        raw = await request.body()
        response = await call_next(request)
        chunks = []
        async for chunk in response.body_iterator:  # type: ignore[attr-defined]
            chunks.append(chunk.encode() if isinstance(chunk, str) else chunk)
        body = b"".join(chunks)
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {
                "raw": raw[:16384].decode("utf-8", errors="replace"),
                "truncated": len(raw) > 16384,
            }
        try:
            returned = json.loads(body)
        except ValueError:
            returned = {
                "raw": body[:16384].decode("utf-8", errors="replace"),
                "truncated": len(body) > 16384,
            }
        parts = request.url.path.split("/")
        camera_id = parts[3] if len(parts) > 3 and parts[2] == "cameras" else None
        trace = HttpTrace(
            trace_id=str(uuid4()),
            run_id=workflow.store.run_id,
            camera_id=camera_id,
            request_id=payload.get("request_id") if isinstance(payload, dict) else None,
            started_at_utc=started,
            finished_at_utc=datetime.now(UTC).isoformat(),
            method=request.method,
            path=getattr(request.state, "external_request_path", request.url.path),
            request_body=payload,
            response_status=response.status_code,
            response_body=returned,
        )
        with workflow.store.transaction() as db:
            workflow.calibration.store._put(db, "http-trace", trace.trace_id, trace)
        return Response(
            body,
            status_code=response.status_code,
            headers=dict(response.headers),
            background=response.background,
        )

    def service() -> CalibrationService:
        if workflow is None or workflow.calibration is None:
            raise CalibrationError(
                "MEASURED_CELL_PROFILE_REQUIRED",
                "Start a test using the synthetic calibration gantry cell",
            )
        return workflow.calibration

    @app.exception_handler(CalibrationError)
    async def calibration_error(request: Request, error: CalibrationError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"reason": error.code, "detail": error.detail})

    @app.get("/calibration")
    def overview() -> dict[str, object]:
        if workflow is None or workflow.calibration is None:
            return {
                "supported": False,
                "scope": "Legacy/HKM observations retain their original provenance",
            }
        selected = service()
        return {
            "supported": True,
            "scope": "Synthetic measurements and simulated operator approval",
            "states": [state.model_dump(mode="json") for state in selected.store.states()],
            "cameras": [
                camera.model_dump(mode="json") for camera in selected.sensor.cameras.values()
            ],
            "board": selected.sensor.board.model_dump(mode="json"),
            "machine": workflow.runtime.world().calibration_machine,
            "seed": selected.sensor.seed,
            "fault_catalogue": catalogue(),
            "capture_scenarios": scenario_options(),
            "investigation_kinds": get_args(InvestigationKind),
            "next_steps": next_steps(selected),
        }

    def next_steps(selected: CalibrationService) -> dict[str, object]:
        with selected.store.store.readonly_connect() as db:
            captures = [
                Capture.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM calibration_records WHERE kind='capture' ORDER BY rowid"
                ).fetchall()
            ]
            quality = [
                AcquisitionReport.model_validate_json(row[0])
                for row in db.execute(
                    "SELECT body FROM calibration_records WHERE kind='acquisition-report' ORDER BY rowid"
                ).fetchall()
            ]
        state_map = {state.camera.camera_id: state for state in selected.store.states()}
        machine = workflow.runtime.world().calibration_machine if workflow else None
        result: dict[str, object] = {}
        for camera_id in selected.sensor.cameras:
            state = state_map.get(camera_id)
            dataset = next(
                (
                    capture.dataset_id
                    for capture in reversed(captures)
                    if capture.camera_id == camera_id and capture.partition == "fit"
                ),
                None,
            )
            info: dict[str, object] = {
                "dataset_id": dataset,
                "revision": state.revision if state else 0,
            }
            if state is None:
                info.update(
                    action="configure",
                    label="Configure camera",
                    detail="Verify RGB/depth optics against a separate synthetic factory fixture, then record the board and simulation-only limits. This does not locate the camera relative to the robot.",
                )
            elif state.camera.fingerprint() != selected.sensor.cameras[camera_id].fingerprint():
                info.update(
                    action="configure",
                    label="Record changed camera model",
                    detail="The reported camera configuration changed. Verify its optics/profile and record it before any installation calibration or target generation.",
                )
            elif state.board.fingerprint() != selected.sensor.board.fingerprint():
                info.update(
                    action="configure",
                    label="Record changed board",
                    detail="The shared board dimensions or mounting identity changed. Record the new specification, then measure and validate a new candidate for each camera. This does not mean the cameras moved.",
                )
            elif state.camera_model_report_id is None:
                info.update(
                    action="configure",
                    label="Verify camera model",
                    detail="This historical configuration has no saved optical verification. Record a current model check before new calibration or execution.",
                )
            elif not selected.store.record(
                "camera-model-report", state.camera_model_report_id, CameraModelReport
            ).passed:
                info.update(
                    action="inspect",
                    label="Inspect camera model",
                    detail="Optical model verification failed. Inspect the profile, crop/resize and camera-model evidence before new measurements.",
                )
            elif state.limits.max_reference_error_mm is None:
                info.update(
                    action="restore-limits",
                    label="Restore documented limits",
                    detail="The reference-error tolerance is missing. Approval and affected targets are blocked. Restore the original simulation budget before new independent validation; this action does not approve calibration.",
                )
            elif state.workflow_state == "INVESTIGATION":
                info.update(
                    action="begin-measurements",
                    label="Start new measurements",
                    detail="Affected targets are blocked. Inspect routine checks, then install the keyed board and measure a new candidate. Old approval cannot authorize these targets.",
                )
            elif state.workflow_state == "UNVERIFIED":
                if machine and not machine.board_mounted:
                    info.update(
                        action="begin-measurements",
                        label="Install calibration board",
                        detail="Install the keyed board and clear the tool check before acquiring calibration measurements.",
                    )
                else:
                    info.update(
                        action="acquire",
                        label="Acquire board images",
                        detail="Move the simulated flange through planned poses and capture RGB and native depth.",
                    )
            elif state.workflow_state == "NEW_MEASUREMENTS":
                measured = next(
                    (
                        item
                        for item in reversed(quality)
                        if item.camera_id == camera_id and item.dataset_id == dataset
                    ),
                    None,
                )
                if measured is not None and not measured.ready_to_fit:
                    info.update(
                        action="begin-measurements",
                        label="Improve measurements",
                        detail=measured.next_action,
                        measurement_report_id=measured.report_id,
                    )
                else:
                    info.update(
                        action="fit",
                        label="Estimate calibration",
                        detail="Fit camera-to-base and board mounting from accepted image measurements. The candidate stays inactive.",
                    )
            elif state.workflow_state == "CANDIDATE":
                info.update(
                    action="validate",
                    label="Validate independently",
                    detail="Freeze the candidate, reserve unused data, and check image chains and independent reference points.",
                )
            elif state.workflow_state == "REJECTED":
                info.update(
                    action="begin-measurements",
                    label="Start new measurements",
                    detail="Validation rejected this candidate. Inspect the failed limits before measuring a replacement with unused validation data.",
                )
            elif state.workflow_state == "INDEPENDENT_VALIDATION":
                if state.report_id and selected.report(state.report_id).passed:
                    info.update(
                        action="approve",
                        label="Approve for this simulation",
                        detail="Record your explicit simulated operator approval of the passing, applicable candidate.",
                    )
                else:
                    info.update(
                        action="pending-validation",
                        label="Validation pending",
                        detail="The reserved validation has not completed. Check the saved request before retrying.",
                    )
            elif state.active_validity == "VERIFIED":
                other = next(
                    (
                        key
                        for key in selected.sensor.cameras
                        if key != camera_id
                        and (key not in state_map or state_map[key].active_validity != "VERIFIED")
                    ),
                    None,
                )
                if other:
                    info.update(
                        action="select-camera",
                        camera_id=other,
                        label="Calibrate the other camera",
                        detail="Each sensor requires its own camera model and approved transform.",
                    )
                elif machine and (machine.board_mounted or not machine.tool_verification_id):
                    info.update(
                        action="tool-check",
                        label="Remove board and check tool",
                        detail="Use independent synthetic pivot and orientation measurements before constructing a grasp.",
                    )
                else:
                    info.update(
                        action="run",
                        label="Run a guided pick",
                        detail="Use the approved camera transform to measure the object, plan a target and inspect the actual command.",
                    )
            else:
                info.update(
                    action="inspect",
                    label="Inspect current state",
                    detail="Review the saved evidence before continuing.",
                )
            result[camera_id] = info
        return result

    @app.get("/calibration/capture-plan")
    def capture_plan() -> dict[str, object]:
        return {
            "classification": "PLANNED_POSES; read-only, no robot movement",
            "poses": [
                pose.model_dump(mode="json") for pose in service().sensor.planned_poses("fit")
            ],
        }

    @app.get("/calibration/export")
    def export() -> Response:
        return Response(
            service().export_zip(),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="calibration-evidence.zip"'},
        )

    @app.post("/calibration/cameras/{camera_id}/configure", response_model=OperationReceipt)
    def configure(camera_id: str, request: Mutation) -> OperationReceipt:
        return service().configure(camera_id, request)

    @app.post("/calibration/cameras/{camera_id}/acquisitions", response_model=OperationReceipt)
    def acquire(camera_id: str, request: AcquireRequest) -> OperationReceipt:
        return service().acquire(
            camera_id,
            request.dataset_id,
            _mutation(request),
            repeated_pose=request.repeated_poses,
            settled=request.settled,
            timestamp_skew_s=request.timestamp_skew_s,
            scenario=request.scenario,
        )

    @app.post("/calibration/cameras/{camera_id}/candidates", response_model=OperationReceipt)
    def fit(camera_id: str, request: FitRequest) -> OperationReceipt:
        return service().fit(
            camera_id, request.dataset_id, request.candidate_id, _mutation(request)
        )

    @app.post("/calibration/cameras/{camera_id}/validations", response_model=OperationReceipt)
    def validate(camera_id: str, request: ValidationRequest) -> OperationReceipt:
        return service().validate(
            camera_id, request.candidate_id, request.dataset_id, _mutation(request)
        )

    @app.post("/calibration/cameras/{camera_id}/reuse-estimate", response_model=OperationReceipt)
    def reuse_estimate(camera_id: str, request: ReuseRequest) -> OperationReceipt:
        return service().reuse_estimate(
            camera_id, request.artifact_id, request.candidate_id, _mutation(request)
        )

    @app.post("/calibration/cameras/{camera_id}/approvals", response_model=OperationReceipt)
    def approve(camera_id: str, request: ApprovalRequest) -> OperationReceipt:
        return service().store.approve(
            camera_id, request.candidate_id, request.report_id, request.actor, _mutation(request)
        )

    @app.post("/calibration/cameras/{camera_id}/tool-check", response_model=OperationReceipt)
    def tool_check(camera_id: str, request: Mutation) -> OperationReceipt:
        return service().prepare_tool(camera_id, request)

    @app.post("/calibration/cameras/{camera_id}/invalidation", response_model=OperationReceipt)
    def invalidate(camera_id: str, request: InvalidationRequest) -> OperationReceipt:
        return service().store.invalidate(camera_id, request.reason, _mutation(request))

    @app.post("/calibration/cameras/{camera_id}/routine-check", response_model=OperationReceipt)
    def routine_check(camera_id: str, request: Mutation) -> OperationReceipt:
        return service().routine_check(camera_id, request)

    @app.post("/calibration/cameras/{camera_id}/move-camera", response_model=OperationReceipt)
    def move_camera(camera_id: str, request: CameraMovementRequest) -> OperationReceipt:
        return service().move_camera(
            camera_id, _mutation(request), request.translation_m, request.rotation_rad
        )

    @app.post("/calibration/cameras/{camera_id}/faults", response_model=OperationReceipt)
    def fault(camera_id: str, request: FaultRequest) -> OperationReceipt:
        return service().introduce_fault(camera_id, request.kind, _mutation(request))

    @app.post(
        "/calibration/cameras/{camera_id}/begin-measurements", response_model=OperationReceipt
    )
    def begin_measurements(camera_id: str, request: Mutation) -> OperationReceipt:
        return service().begin_measurements(camera_id, request)

    @app.post("/calibration/cameras/{camera_id}/investigate", response_model=OperationReceipt)
    def investigate(camera_id: str, request: InvestigationRequest) -> OperationReceipt:
        return service().investigate(camera_id, request.kind, request.identity, _mutation(request))

    @app.get("/calibration/records")
    def record_index() -> list[dict[str, object]]:
        with service().store.store.readonly_connect() as db:
            rows = db.execute(
                "SELECT kind,id,fingerprint,body FROM calibration_records ORDER BY rowid"
            ).fetchall()
        decoded = [(row, json.loads(row[3])) for row in rows]
        camera_by_candidate = {
            body["candidate_id"]: body["camera"]["camera_id"]
            for row, body in decoded
            if row[0] == "candidate"
        }
        trace_by_result = {}
        for row, body in decoded:
            if row[0] == "calculation-trace":
                for key in result_record_keys(ComputationTrace.model_validate(body)):
                    trace_by_result[key] = row[1]
        return [
            {
                "kind": row[0],
                "id": row[1],
                "sha256": row[2],
                "camera_id": body.get("camera_id")
                or body.get("camera", {}).get("camera_id")
                or body.get("candidate", {}).get("camera", {}).get("camera_id")
                or camera_by_candidate.get(body.get("candidate_id")),
                "dataset_id": body.get("dataset_id"),
                "partition": body.get("partition"),
                "source_trace_id": trace_by_result.get((row[0], row[1])),
            }
            for row, body in decoded
            if row[0] in get_args(RecordKind)
        ]

    @app.get("/calibration/operations/{camera_id}/{request_id}")
    def operation(camera_id: str, request_id: str) -> dict[str, object]:
        with service().store.store.readonly_connect() as db:
            row = db.execute(
                "SELECT body FROM calibration_operations WHERE camera_id=? AND request_id=?",
                (camera_id, request_id),
            ).fetchone()
        if row is None:
            raise NotFound(request_id)
        body: dict[str, object] = json.loads(row[0])
        return body

    @app.get("/calibration/records/{kind}/{identity}")
    def record(kind: RecordKind, identity: str) -> dict[str, object]:
        with service().store.store.readonly_connect() as db:
            row = db.execute(
                "SELECT body FROM calibration_records WHERE kind=? AND id=?", (kind, identity)
            ).fetchone()
        if row is None:
            raise NotFound(identity)
        body: dict[str, object] = json.loads(row[0])
        return body

    @app.get("/calibration/source")
    def source(path: str, symbol: str) -> dict[str, object]:
        return {
            **source_snapshot(path, symbol),
            "scope": "Current reference source, not a saved execution snapshot",
        }

    @app.get("/calibration/captures/{capture_id}/depth-display")
    def capture_depth_display(capture_id: Id) -> DepthDisplay:
        selected = service()
        capture = selected.store.record("capture", capture_id, Capture)
        return depth_display(selected.artifacts.read_depth(capture.depth))

    @app.get("/calibration/captures/{capture_id}/{view}")
    def capture_image(
        capture_id: str, view: Literal["rgb", "depth", "corners", "raw-depth"]
    ) -> Response:
        selected = service()
        capture = selected.store.record("capture", capture_id, Capture)
        if view == "raw-depth":
            return Response(
                selected.artifacts.read(capture.depth),
                media_type="application/x-npy",
                headers={
                    "Content-Disposition": f'attachment; filename="{capture.capture_id}-native-depth.npy"'
                },
            )
        if view == "rgb":
            return Response(selected.artifacts.read(capture.rgb), media_type="image/png")
        if view == "corners":
            rgb = selected.artifacts.read_rgb(capture.rgb)
            try:
                sample = selected.store.record("sample", capture_id, PoseSample)
            except NotFound:
                raise CalibrationError(
                    "NO_ACCEPTED_CORNER_OVERLAY", "Inspect the saved image and rejection reason"
                ) from None
            cv2.aruco.drawDetectedCornersCharuco(
                rgb,
                np.asarray(sample.image_points_px, dtype=np.float32).reshape(-1, 1, 2),
                np.asarray(sample.corner_ids, dtype=np.int32).reshape(-1, 1),
            )
            if sample.excluded_image_points_px is not None:
                for identity, point in zip(
                    sample.excluded_corner_ids, sample.excluded_image_points_px, strict=True
                ):
                    pixel = tuple(int(round(value)) for value in point)
                    cv2.drawMarker(rgb, pixel, (255, 180, 0), cv2.MARKER_TILTED_CROSS, 14, 2)
                    cv2.putText(
                        rgb,
                        f"X{identity}",
                        (pixel[0] + 5, pixel[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        (255, 180, 0),
                        1,
                    )
            pixels = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        else:
            pixels = depth_preview(selected.artifacts.read_depth(capture.depth))
        success, encoded = cv2.imencode(".png", pixels)
        if not success:
            raise CalibrationError("EVIDENCE_PREVIEW_ENCODING_FAILED")
        return Response(encoded.tobytes(), media_type="image/png")

    @app.get("/calibration/inspect-pixel")
    def point_inspection(
        capture_id: Id,
        artifact_id: Id,
        u: float = Query(ge=0, le=4096),
        v: float = Query(ge=0, le=4096),
        mode: Literal["native", "aligned"] = "native",
    ) -> dict[str, object]:
        selected = service()
        capture = selected.store.record("capture", capture_id, Capture)
        artifact = selected.store.record("artifact", artifact_id, CalibrationArtifact)
        limits = selected.store.record("limits", artifact.candidate.limits_fingerprint, Limits)
        return inspect_pixel(capture, artifact, limits, selected.artifacts, (u, v), mode)

    @app.get("/calibration/geometry", response_model=EvidenceGeometry)
    def geometry(
        camera_id: Id,
        mode: Literal["capture", "poses", "record"],
        capture_id: Id | None = None,
        record_kind: Literal["sample", "validation", "routine-check", "runtime-target"]
        | None = None,
        record_id: Id | None = None,
    ) -> EvidenceGeometry:
        selected = service()
        if mode in {"capture", "poses"}:
            if capture_id is None:
                raise CalibrationError("SELECT_A_SAVED_CAPTURE")
            capture = selected.store.record("capture", capture_id, Capture)
            if capture.camera_id != camera_id:
                raise CalibrationError("CAPTURE_CAMERA_MISMATCH")
            if mode == "capture":
                saved_scene = getattr(selected.sensor, "capture_presentation", None)
                if not callable(saved_scene):
                    raise CalibrationError("SAVED_CAPTURE_SCENE_UNAVAILABLE")
                return capture_geometry(saved_scene(capture_id), capture)
            with selected.store.store.readonly_connect() as db:
                plans = [
                    CapturePlan.model_validate_json(row[0])
                    for row in db.execute(
                        "SELECT body FROM calibration_records WHERE kind='capture-plan'"
                    )
                ]
                samples = tuple(
                    PoseSample.model_validate_json(row[0])
                    for row in db.execute(
                        "SELECT body FROM calibration_records WHERE kind='sample'"
                    )
                )
            plan = next(
                (
                    item
                    for item in plans
                    if item.dataset_id == capture.dataset_id and item.camera_id == camera_id
                ),
                None,
            )
            if plan is None:
                raise CalibrationError(
                    "SAVED_CAPTURE_PLAN_UNAVAILABLE",
                    "Select a board training capture to inspect its saved acquisition plan.",
                )
            return pose_geometry(
                plan,
                tuple(
                    item
                    for item in samples
                    if item.camera_id == camera_id and item.dataset_id == capture.dataset_id
                ),
            )
        if record_kind is None or record_id is None:
            raise CalibrationError(
                "SELECT_GEOMETRIC_EVIDENCE",
                "Select a sample, validation, routine check or runtime target in Inspect evidence.",
            )
        if record_kind == "sample":
            sample = selected.store.record("sample", record_id, PoseSample)
            with selected.store.store.readonly_connect() as db:
                candidates = [
                    Candidate.model_validate_json(row[0])
                    for row in db.execute(
                        "SELECT body FROM calibration_records WHERE kind='candidate' ORDER BY rowid DESC"
                    )
                ]
            candidate = next(
                (item for item in candidates if sample.capture_id in item.sample_ids), None
            )
            if sample.camera_id != camera_id or candidate is None:
                raise CalibrationError("SAMPLE_CANDIDATE_UNAVAILABLE")
            evidence = sample_geometry(sample, candidate)
            saved_scene = getattr(selected.sensor, "capture_presentation", None)
            if callable(saved_scene):
                try:
                    background = saved_scene(sample.capture_id).scene
                    evidence = evidence.model_copy(update={"scene": background})
                except CalibrationError as error:
                    if error.code != "SAVED_CAPTURE_SCENE_UNAVAILABLE":
                        raise
            return evidence
        if record_kind == "runtime-target":
            target = selected.store.record("runtime-target", record_id, TargetPose)
            with selected.store.store.readonly_connect() as db:
                calls = [
                    ComputationTrace.model_validate_json(row[0])
                    for row in db.execute(
                        "SELECT body FROM calibration_records WHERE kind='calculation-trace'"
                    )
                ]
            target_call = next(
                (
                    call
                    for call in calls
                    if call.camera_id == camera_id
                    and (record_kind, record_id) in result_record_keys(call)
                ),
                None,
            )
            if target_call is None:
                raise CalibrationError("TARGET_CAMERA_MISMATCH")
            evidence = target_geometry(target, record_id)
            job_id = target_call.inputs.get("job_id")
            if isinstance(job_id, str):
                try:
                    background = selected.store.store.load(VisualScene, job_id)
                    evidence = evidence.model_copy(update={"scene": background})
                except NotFound:
                    pass  # Older evidence: show coordinates only, never today's cell.
            return evidence
        if record_kind == "validation":
            report = selected.store.record("validation", record_id, ValidationReport)
            candidate = selected.store.record("candidate", report.candidate_id, Candidate)
            if candidate.camera.camera_id != camera_id:
                raise CalibrationError("REPORT_CAMERA_MISMATCH")
            return reference_geometry(report.references, report.report_id)
        check = selected.store.record("routine-check", record_id, RoutineCheck)
        if check.camera_id != camera_id:
            raise CalibrationError("REPORT_CAMERA_MISMATCH")
        return reference_geometry(check.references, check.check_id)
