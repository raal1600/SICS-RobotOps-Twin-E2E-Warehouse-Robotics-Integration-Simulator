"""Shared application/CLI orchestration for the measured calibration lifecycle.

The synthetic adapter is composed here, outside the numerical estimator. It supplies
captures and public configurations only. The instructor oracle is never imported.
"""

import hashlib
import json
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

from robotops.calibration.acquisition import CaptureScenario, assess, make_plan
from robotops.calibration.artifacts import SensorArtifacts
from robotops.calibration.checks import evaluate_references
from robotops.calibration.contracts import (
    ArtifactRef,
    Calculation,
    CalibrationArtifact,
    Candidate,
    Capture,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PoseSample,
    Record,
    ReferenceBatch,
    ReferenceCapture,
    SurfaceDetection,
    Transform,
    ValidationReport,
)
from robotops.calibration.depth import reconstruct
from robotops.calibration.diagnostics import InvestigationKind, investigate
from robotops.calibration.errors import CalibrationError
from robotops.calibration.estimation import estimate_board, fit
from robotops.calibration.faults import FaultKind, FaultRecord, definition
from robotops.calibration.investigation import saved_inputs
from robotops.calibration.lifecycle import CalibrationStore, CameraState, Mutation, OperationReceipt
from robotops.calibration.optics import OpticsLimits, verify_camera_model
from robotops.calibration.outcome import PickOutcome, summarize_pick
from robotops.calibration.perception import identify_surface
from robotops.calibration.synthetic import SyntheticSensorWorld
from robotops.calibration.tcp import ToolMeasurements, ToolVerification, verify_measurements
from robotops.calibration.trace import recorded_call
from robotops.calibration.validation import validate
from robotops.domain.models import (
    CommandReceipt,
    RobotCommand,
    VerificationResult,
    WorldObservation,
)
from robotops.workflow.store import Conflict, Store


class ServiceIntent(Record):
    operation: str
    request: Mutation
    arguments: dict[str, object]


class CalibrationService:
    def __init__(self, store: Store, seed: int, sensor: SyntheticSensorWorld | None = None):
        self.store = CalibrationStore(store)
        self.artifacts = SensorArtifacts(store.path.parent / "calibration" / "images")
        with store.transaction() as db:
            prior = db.execute("SELECT value FROM meta WHERE key='calibration_seed'").fetchone()
            if prior and int(prior[0]) != seed:
                raise Conflict("CALIBRATION_WORLD_SEED_IMMUTABLE")
            db.execute("INSERT OR IGNORE INTO meta VALUES ('calibration_seed',?)", (str(seed),))
        self.sensor = sensor or SyntheticSensorWorld(seed, self.artifacts)

    def configure(self, camera_id: str, request: Mutation) -> OperationReceipt:
        refresh = getattr(self.sensor, "refresh_configuration", None)
        if callable(refresh):
            refresh()
        if camera_id not in self.sensor.cameras:
            raise CalibrationError("UNKNOWN_SYNTHETIC_CAMERA")
        camera = self.sensor.cameras[camera_id]
        references = self.sensor.optical_references(camera_id)
        identity = "optics-" + camera.fingerprint()[:32]
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/optics.py",
            "verify_camera_model",
            {
                "camera": camera.model_dump(mode="json"),
                "references": [item.model_dump(mode="json") for item in references],
                "limits": OpticsLimits().model_dump(mode="json"),
            },
            partial(verify_camera_model, camera, references, OpticsLimits(), identity),
        )
        return self.store.configure(
            camera, self.sensor.board, Limits(), request, report, references
        )

    def _saved(
        self, camera_id: str, operation: str, request: Mutation, arguments: dict[str, object]
    ) -> OperationReceipt | None:
        with self.store.store.readonly_connect() as db:
            row = db.execute(
                "SELECT body FROM calibration_operations WHERE camera_id=? AND request_id=?",
                (camera_id, request.request_id),
            ).fetchone()
            if row is None:
                return None
            receipt = OperationReceipt.model_validate_json(row[0])
            argument_row = db.execute(
                "SELECT body FROM calibration_records WHERE kind='service-request' AND id=?",
                (f"{camera_id}:{request.request_id}",),
            ).fetchone()
            expected = ServiceIntent(
                operation=operation, request=request, arguments=arguments
            ).model_dump(mode="json")
            if (
                receipt.operation != operation
                or argument_row is None
                or json.loads(argument_row[0]) != expected
            ):
                raise Conflict("CALIBRATION_IDEMPOTENCY_CONFLICT")
            return receipt

    def _request(
        self, camera_id: str, operation: str, request: Mutation, arguments: dict[str, object]
    ) -> None:
        # Reserve only the request identity. Heavy sensor/numerical work occurs outside
        # the transaction; final commit still uses the original expected revision.
        intent = ServiceIntent(operation=operation, request=request, arguments=arguments)
        value = intent.model_dump_json()
        identity = f"{camera_id}:{request.request_id}"
        with self.store.store.transaction() as db:
            row = db.execute(
                "SELECT body FROM calibration_records WHERE kind='service-request' AND id=?",
                (identity,),
            ).fetchone()
            if row:
                if row[0] != value:
                    raise Conflict("CALIBRATION_IDEMPOTENCY_CONFLICT")
                return
            if self.store.state(camera_id).revision != request.expected_revision:
                raise Conflict("STALE_CALIBRATION_REVISION")
            self.store._put(db, "service-request", identity, intent)

    def _capture_call(
        self,
        state: CameraState,
        pose: Transform,
        dataset_id: str,
        index: int,
        partition: Literal["fit", "validation"],
        request_id: str,
        *,
        settled: bool = True,
        timestamp_skew_s: float = 0,
    ) -> Capture:
        method = self.sensor.acquire
        return recorded_call(
            self.store,
            state.camera.camera_id,
            request_id,
            method.__module__.replace(".", "/") + ".py",
            method.__qualname__,
            {
                "camera_id": state.camera.camera_id,
                "flange": pose.model_dump(mode="json"),
                "dataset_id": dataset_id,
                "index": index,
                "partition": partition,
                "limits": state.limits.model_dump(mode="json"),
                "settled": settled,
                "timestamp_skew_s": timestamp_skew_s,
            },
            partial(
                method,
                state.camera.camera_id,
                pose,
                dataset_id,
                index,
                partition,
                state.limits,
                settled=settled,
                timestamp_skew_s=timestamp_skew_s,
            ),
        )

    def _board_sample(self, state: CameraState, capture: Capture, request_id: str) -> PoseSample:
        return recorded_call(
            self.store,
            state.camera.camera_id,
            request_id,
            "robotops/calibration/estimation.py",
            "estimate_board",
            {
                "capture": capture.model_dump(mode="json"),
                "camera": state.camera.model_dump(mode="json"),
                "board": state.board.model_dump(mode="json"),
                "limits": state.limits.model_dump(mode="json"),
            },
            partial(
                estimate_board,
                capture,
                self.artifacts.read_rgb(capture.rgb),
                state.camera,
                state.board,
                state.limits,
            ),
        )

    def _reference_batch(
        self,
        state: CameraState,
        dataset_id: str,
        partition: Literal["validation", "routine"],
        request_id: str,
    ) -> ReferenceBatch:
        method = self.sensor.reference_batch
        batch = recorded_call(
            self.store,
            state.camera.camera_id,
            request_id,
            method.__module__.replace(".", "/") + ".py",
            method.__qualname__,
            {"camera_id": state.camera.camera_id, "dataset_id": dataset_id, "partition": partition},
            partial(method, state.camera.camera_id, dataset_id, partition),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "reference-batch", batch.batch_id, batch)
            for item in batch.captures:
                self.store._put(db, "capture", item.capture.capture_id, item.capture)
        return batch

    def _reference_measurement(
        self,
        state: CameraState,
        reference: ReferenceCapture,
        x: Transform,
        request_id: str,
        estimate_id: str,
    ) -> IndependentReference:
        capture = reference.capture
        if (
            capture.configuration_fingerprint != state.camera.fingerprint()
            or capture.board_fingerprint != state.board.fingerprint()
            or capture.camera_id != state.camera.camera_id
        ):
            raise CalibrationError("REFERENCE_CAPTURE_CONFIGURATION_CHANGED")
        if not capture.admitted:
            raise CalibrationError("CAPTURE_NOT_ADMITTED", ", ".join(capture.rejection_codes))
        detection = recorded_call(
            self.store,
            capture.camera_id,
            request_id,
            "robotops/calibration/perception.py",
            "identify_surface",
            {
                "capture_id": capture.capture_id,
                "camera_id": capture.camera_id,
                "rgb": capture.rgb.model_dump(mode="json"),
                "method": "reference_center",
            },
            partial(
                identify_surface,
                capture.capture_id,
                capture.camera_id,
                self.artifacts.read_rgb(capture.rgb),
                "reference_center",
                self.artifacts,
            ),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "surface-detection", capture.capture_id, detection)
        measurement = recorded_call(
            self.store,
            capture.camera_id,
            request_id,
            "robotops/calibration/depth.py",
            "reconstruct",
            {
                "capture_id": capture.capture_id,
                "selected_rgb_pixel": detection.selected_rgb_pixel,
                "depth": capture.depth.model_dump(mode="json"),
                "rgb_surface_mask": detection.mask.model_dump(mode="json"),
                "camera": state.camera.model_dump(mode="json"),
                "x": x.model_dump(mode="json"),
                "limits": state.limits.model_dump(mode="json"),
                "estimate_id": estimate_id,
                "independent_surveyed_base_point_m": reference.base_point_m,
                "scope": "Non-authorizing reference reconstruction; survey coordinate is compared later, not an input to reconstruct",
            },
            partial(
                reconstruct,
                detection.selected_rgb_pixel,
                self.artifacts.read_depth(capture.depth),
                state.camera,
                x,
                state.limits,
                rgb_surface_mask=self.artifacts.read_mask(detection.mask),
            ),
        )
        result = IndependentReference(
            reference_id=reference.reference_id,
            dataset_id=capture.dataset_id,
            base_point_m=reference.base_point_m,
            measurement=measurement,
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "reference", result.reference_id, result)
        return result

    def acquire(
        self,
        camera_id: str,
        dataset_id: str,
        request: Mutation,
        *,
        repeated_pose: bool = False,
        timestamp_skew_s: float = 0,
        settled: bool = True,
        scenario: CaptureScenario = "varied",
    ) -> OperationReceipt:
        arguments: dict[str, object] = {
            "dataset_id": dataset_id,
            "repeated_pose": repeated_pose,
            "timestamp_skew_s": timestamp_skew_s,
            "settled": settled,
        }
        if scenario != "varied":
            arguments["scenario"] = scenario
        previous = self._saved(camera_id, "acquire", request, arguments)
        if previous:
            return previous
        self._request(camera_id, "acquire", request, arguments)
        state = self.store.state(camera_id)
        self.store.require_camera_model(state)
        if repeated_pose and scenario not in {"varied", "repeated"}:
            raise CalibrationError("CONFLICTING_CAPTURE_SCENARIOS")
        poses = self.sensor.planned_poses("fit")
        plan = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/acquisition.py",
            "make_plan",
            {
                "dataset_id": dataset_id,
                "scenario": "repeated" if repeated_pose else scenario,
                "camera": state.camera.model_dump(mode="json"),
                "board": state.board.model_dump(mode="json"),
                "poses": [pose.model_dump(mode="json") for pose in poses],
                "settled": settled,
                "timestamp_skew_s": timestamp_skew_s,
            },
            partial(
                make_plan,
                dataset_id,
                state.camera,
                state.board,
                poses,
                "repeated" if repeated_pose else scenario,
                settled=settled,
                timestamp_skew_s=timestamp_skew_s,
            ),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "capture-plan", plan.plan_id, plan)
        captures, samples, rejected = [], [], []
        for index, pose in enumerate(plan.flange_poses):
            capture = self._capture_call(
                state,
                pose,
                dataset_id,
                index,
                "fit",
                request.request_id,
                settled=plan.settled,
                timestamp_skew_s=plan.timestamp_skew_s,
            )
            captures.append(capture)
            try:
                samples.append(self._board_sample(state, capture, request.request_id))
            except CalibrationError as error:
                rejected.append(
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
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/acquisition.py",
            "assess",
            {
                "plan_id": plan.plan_id,
                "capture_ids": [item.capture_id for item in captures],
                "sample_ids": [item.capture_id for item in samples],
                "rejections": [item.model_dump(mode="json") for item in rejected],
                "limits": state.limits.model_dump(mode="json"),
            },
            partial(assess, plan, captures, samples, rejected, state.camera, state.limits),
        )
        return self.store.save_measurements(
            camera_id, captures, samples, rejected, request, plan, report
        )

    def fit(
        self, camera_id: str, dataset_id: str, candidate_id: str, request: Mutation
    ) -> OperationReceipt:
        arguments: dict[str, object] = {"dataset_id": dataset_id, "candidate_id": candidate_id}
        previous = self._saved(camera_id, "fit", request, arguments)
        if previous:
            return previous
        self._request(camera_id, "fit", request, arguments)
        state = self.store.state(camera_id)
        self.store.require_camera_model(state)
        with self.store.store.readonly_connect() as db:
            rows = db.execute(
                "SELECT body FROM calibration_records WHERE kind='sample' ORDER BY id"
            ).fetchall()
        samples = [PoseSample.model_validate_json(row[0]) for row in rows]
        selected = [
            sample
            for sample in samples
            if sample.dataset_id == dataset_id and sample.camera_id == camera_id
        ]
        candidate = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/estimation.py",
            "fit",
            {
                "sample_ids": [sample.capture_id for sample in selected],
                "camera": state.camera.model_dump(mode="json"),
                "board": state.board.model_dump(mode="json"),
                "limits": state.limits.model_dump(mode="json"),
                "known_mount": None,
                "candidate_id": candidate_id,
            },
            partial(fit, selected, state.camera, state.board, state.limits, candidate_id),
        )
        return self.store.save_candidate(candidate, request)

    def validate(
        self, camera_id: str, candidate_id: str, dataset_id: str, request: Mutation
    ) -> OperationReceipt:
        arguments: dict[str, object] = {"candidate_id": candidate_id, "dataset_id": dataset_id}
        previous = self._saved(camera_id, "validate", request, arguments)
        if previous:
            return previous
        # A reservation survives restart and retry, and binds this holdout to one frozen candidate.
        reservation_id = (
            "reserve-" + hashlib.sha256(f"{camera_id}/{request.request_id}".encode()).hexdigest()
        )
        reservation_request = Mutation(
            request_id=reservation_id, expected_revision=request.expected_revision
        )
        self._request(camera_id, "validate", request, arguments)
        datasets = (f"{dataset_id}-board", f"{dataset_id}-references")
        reservation = self.store.reserve_validation(
            camera_id, candidate_id, datasets, reservation_request
        )
        state = reservation.state
        candidate = self.store.record("candidate", candidate_id, Candidate)
        captures: list[Capture] = []
        samples: list[PoseSample] = []
        rejected: list[MeasurementRejection] = []
        for index, pose in enumerate(self.sensor.planned_poses("validation")):
            capture = self._capture_call(
                state, pose, datasets[0], index, "validation", request.request_id
            )
            captures.append(capture)
            try:
                samples.append(self._board_sample(state, capture, request.request_id))
            except CalibrationError as error:
                rejected.append(
                    MeasurementRejection(
                        capture_id=capture.capture_id,
                        reason=error.code,
                        detail=error.detail,
                        calculation=Calculation.model_validate(error.calculation)
                        if error.calculation
                        else None,
                        stage="board_pose",
                    )
                )
        references = []
        batch = self._reference_batch(state, datasets[1], "validation", request.request_id)
        for reference in batch.captures:
            captures.append(reference.capture)
            try:
                references.append(
                    self._reference_measurement(
                        state, reference, candidate.x, request.request_id, candidate_id
                    )
                )
            except CalibrationError as error:
                rejected.append(
                    MeasurementRejection(
                        capture_id=reference.capture.capture_id,
                        reason=error.code,
                        detail=error.detail,
                        calculation=Calculation.model_validate(error.calculation)
                        if error.calculation
                        else None,
                        stage="depth",
                    )
                )
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/validation.py",
            "validate",
            {
                "candidate": candidate.model_dump(mode="json"),
                "sample_ids": [s.capture_id for s in samples],
                "reference_ids": [r.reference_id for r in references],
                "limits": state.limits.model_dump(mode="json"),
            },
            partial(
                validate,
                candidate,
                samples,
                references,
                state.limits,
                f"report-{candidate_id}-{request.request_id}",
                rejected,
            ),
        )
        # The completion is the second revision of one user action; duplicate request
        # lookup above still binds to the original client request, not this internal revision.
        return self.store.save_validation(
            camera_id,
            reservation_id,
            report,
            captures,
            samples,
            references,
            Mutation(request_id=request.request_id, expected_revision=state.revision),
        )

    def reuse_estimate(
        self, camera_id: str, artifact_id: str, candidate_id: str, request: Mutation
    ) -> OperationReceipt:
        action = getattr(self.sensor, "mount_board", None)
        if not callable(action):
            raise CalibrationError("CONTROLLER_SENSOR_ADAPTER_REQUIRED")
        arguments: dict[str, object] = {"artifact_id": artifact_id, "candidate_id": candidate_id}
        previous = self._saved(camera_id, "reuse-estimate", request, arguments)
        if previous:
            action(request.request_id)
            return previous
        refresh = getattr(self.sensor, "refresh_configuration", None)
        if callable(refresh):
            refresh()
        state = self.store.state(camera_id)
        if (
            state.camera.fingerprint() != self.sensor.cameras[camera_id].fingerprint()
            or state.board.fingerprint() != self.sensor.board.fingerprint()
        ):
            raise CalibrationError("CANDIDATE_CONFIGURATION_NOT_APPLICABLE")
        self._request(camera_id, "reuse-estimate", request, arguments)
        receipt = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/lifecycle.py",
            "CalibrationStore.reuse_estimate",
            {
                **arguments,
                "original_artifact": self.store.record(
                    "artifact", artifact_id, CalibrationArtifact
                ).model_dump(mode="json"),
            },
            partial(self.store.reuse_estimate, camera_id, artifact_id, candidate_id, request),
        )
        # The keyed fixture's mounting identity is unchanged. Mounting clears the
        # independent tool check; validation/approval cannot make the robot ready alone.
        action(request.request_id)
        return receipt

    def evidence_manifest(self) -> dict[str, object]:
        with self.store.store.readonly_connect() as db:
            db.execute("BEGIN")
            rows = db.execute(
                "SELECT kind,id,fingerprint,body FROM calibration_records ORDER BY kind,id"
            ).fetchall()
            operations = db.execute(
                "SELECT body FROM calibration_operations ORDER BY camera_id,request_id"
            ).fetchall()
            states = db.execute("SELECT body FROM calibration_cameras ORDER BY id").fetchall()
            application_records = db.execute(
                "SELECT kind,id,body FROM records ORDER BY kind,id"
            ).fetchall()
        telemetry = getattr(self.sensor, "evidence_snapshot", None)
        return {
            "format": "robotops-calibration-evidence-1",
            "run_id": self.store.store.run_id,
            "snapshot_scope": "Separate consistent read-only application and controller snapshots; export after operations finish for a complete run",
            "controller": telemetry() if callable(telemetry) else None,
            "seed": self.sensor.seed,
            "states": [json.loads(row[0]) for row in states],
            "records": [
                {"kind": row[0], "id": row[1], "sha256": row[2], "body": json.loads(row[3])}
                for row in rows
            ],
            "operations": [json.loads(row[0]) for row in operations],
            "application_records": [
                {"kind": row[0], "id": row[1], "body": json.loads(row[2])}
                for row in application_records
            ],
        }

    @staticmethod
    def _export_captures(manifest: dict[str, object]) -> list[Capture]:
        records = manifest["records"]
        if not isinstance(records, list):
            raise CalibrationError("INVALID_EVIDENCE_MANIFEST")
        return [
            Capture.model_validate(item["body"]) for item in records if item["kind"] == "capture"
        ]

    @classmethod
    def _export_artifacts(cls, manifest: dict[str, object]) -> list[ArtifactRef]:
        references = [
            ref
            for capture in cls._export_captures(manifest)
            for ref in (capture.rgb, capture.depth)
        ]
        records = manifest["records"]
        if not isinstance(records, list):
            raise CalibrationError("INVALID_EVIDENCE_MANIFEST")
        references.extend(
            SurfaceDetection.model_validate(item["body"]).mask
            for item in records
            if item["kind"] == "surface-detection"
        )
        return references

    def export_zip(self) -> bytes:
        """GET/export creates an in-memory download; it never writes run files or state."""
        manifest = self.evidence_manifest()
        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=3) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            seen = set()
            for ref in self._export_artifacts(manifest):
                if ref.path not in seen:
                    archive.writestr("images/" + ref.path, self.artifacts.read(ref))
                    seen.add(ref.path)
        return output.getvalue()

    def export(self, directory: Path) -> Path:
        """Read-only source-linked records plus referenced raw bytes; never mutates lifecycle."""
        directory.mkdir(parents=True, exist_ok=False)
        manifest = self.evidence_manifest()
        for ref in self._export_artifacts(manifest):
            target = directory / "images" / ref.path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(self.artifacts.read(ref))
        path = directory / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    def report(self, report_id: str) -> ValidationReport:
        return self.store.record("validation", report_id, ValidationReport)

    def prepare_tool(self, camera_id: str, request: Mutation) -> OperationReceipt:
        previous = self._saved(camera_id, "verify-tool", request, {})
        measure = getattr(self.sensor, "measure_tool", None)
        apply = getattr(self.sensor, "apply_tool_check", None)
        if not callable(measure) or not callable(apply):
            raise CalibrationError("CONTROLLER_METROLOGY_ADAPTER_REQUIRED")
        if previous:
            identity = previous.record_ids[0]
            report = self.store.record("tool-verification", identity, ToolVerification)
            measurements = self.store.record("tool-measurements", identity, ToolMeasurements)
            apply(measurements, report)
            return previous
        self._request(camera_id, "verify-tool", request, {})
        self.store.active(camera_id)
        identity = (
            "tool-" + hashlib.sha256(f"{camera_id}:{request.request_id}".encode()).hexdigest()[:32]
        )
        measurements = ToolMeasurements.model_validate(measure(identity).model_dump())
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/tcp.py",
            "verify_measurements",
            {"measurements": measurements.model_dump(mode="json")},
            partial(verify_measurements, measurements),
        )
        receipt = self.store.save_tool_check(camera_id, report, request, measurements)
        apply(measurements, report)
        return receipt

    def routine_check(self, camera_id: str, request: Mutation) -> OperationReceipt:
        previous = self._saved(camera_id, "routine-check", request, {})
        if previous:
            return previous
        self._request(camera_id, "routine-check", request, {})
        state = self.store.state(camera_id)
        if state.active_artifact_id is None:
            raise CalibrationError("APPROVED_CALIBRATION_REQUIRED")
        artifact = self.store.record("artifact", state.active_artifact_id, CalibrationArtifact)
        references, failed = [], []
        batch = self._reference_batch(
            state, f"routine-{request.request_id}", "routine", request.request_id
        )
        for item in batch.captures:
            capture = item.capture
            try:
                reference = self._reference_measurement(
                    state, item, artifact.candidate.x, request.request_id, artifact.artifact_id
                )
                references.append(reference)
            except CalibrationError as error:
                failed.append(capture.capture_id)
                with self.store.store.transaction() as db:
                    self.store._put(
                        db,
                        "rejection",
                        capture.capture_id,
                        MeasurementRejection(
                            capture_id=capture.capture_id,
                            stage="depth",
                            reason=error.code,
                            detail=error.detail,
                            calculation=Calculation.model_validate(error.calculation)
                            if error.calculation
                            else None,
                        ),
                    )
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/checks.py",
            "evaluate_references",
            {
                "references": [item.model_dump(mode="json") for item in references],
                "failed_capture_ids": failed,
                "limits": state.limits.model_dump(mode="json"),
                "artifact_id": artifact.artifact_id,
            },
            partial(
                evaluate_references,
                f"check-{request.request_id}",
                camera_id,
                artifact.artifact_id,
                tuple(references),
                tuple(failed),
                state.limits,
            ),
        )
        return self.store.save_routine_check(report, request, tuple(references))

    def move_camera(
        self,
        camera_id: str,
        request: Mutation,
        translation_m: tuple[float, float, float],
        rotation_rad: tuple[float, float, float],
    ) -> OperationReceipt:
        action = getattr(self.sensor, "move_camera", None)
        if not callable(action):
            raise CalibrationError("CONTROLLER_SENSOR_ADAPTER_REQUIRED")
        self._request(
            camera_id,
            "move-camera",
            request,
            {"translation_m": list(translation_m), "rotation_rad": list(rotation_rad)},
        )
        # Persist the known physical-change notice first. A crash cannot leave the
        # affected artifact authorizing targets after the mount moved.
        receipt = self.store.invalidate(
            camera_id, "KNOWN_CAMERA_MOUNT_CHANGE_REQUIRES_MEASUREMENTS", request
        )
        action(camera_id, request.request_id, translation_m, rotation_rad)
        return receipt

    def introduce_fault(
        self, camera_id: str, kind: FaultKind, request: Mutation
    ) -> OperationReceipt:
        described = definition(kind)
        action = getattr(self.sensor, "apply_fault", None)
        if described.affected != "limits" and not callable(action):
            raise CalibrationError("CONTROLLER_SENSOR_ADAPTER_REQUIRED")
        self._request(camera_id, "simulation-fault", request, {"kind": kind})
        identity = (
            "fault-" + hashlib.sha256(f"{camera_id}:{request.request_id}".encode()).hexdigest()[:32]
        )
        fault = FaultRecord(fault_id=identity, camera_id=camera_id, definition=described)
        # A sensor notice blocks applicability durably before changing physical outputs.
        # Tool changes clear only the tool interlock; camera estimates remain untouched.
        receipt = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/lifecycle.py",
            "CalibrationStore.fault_notice",
            {"fault": fault.model_dump(mode="json"), "request": request.model_dump(mode="json")},
            partial(self.store.fault_notice, fault, request),
        )
        if described.affected != "limits" and callable(action):
            action(fault)
        return receipt

    def record_pick_outcome(
        self,
        command: RobotCommand,
        receipt: CommandReceipt | None,
        observation: WorldObservation,
        verification: VerificationResult,
    ) -> PickOutcome:
        if command.calibrated_plan is None:
            raise CalibrationError("MEASURED_PICK_REQUIRED")
        camera_id = command.calibrated_plan.observed_object.binding.camera_id
        result = recorded_call(
            self.store,
            camera_id,
            verification.verification_id,
            "robotops/calibration/outcome.py",
            "summarize_pick",
            {
                "command": command.model_dump(mode="json"),
                "receipt": receipt.model_dump(mode="json") if receipt else None,
                "observation": observation.model_dump(mode="json"),
                "verification": verification.model_dump(mode="json"),
            },
            partial(summarize_pick, command, receipt, observation, verification),
        )
        with self.store.store.transaction() as db:
            self.store._put(db, "pick-outcome", result.outcome_id, result)
        return result

    def investigate(
        self, camera_id: str, kind: InvestigationKind, identity: str, request: Mutation
    ) -> OperationReceipt:
        arguments: dict[str, object] = {"kind": kind, "identity": identity}
        previous = self._saved(camera_id, "investigate", request, arguments)
        if previous:
            return previous
        self._request(camera_id, "investigate", request, arguments)
        inputs = saved_inputs(self.store, camera_id, kind, identity)
        report_id = (
            "investigation-"
            + hashlib.sha256(f"{camera_id}:{request.request_id}".encode()).hexdigest()[:32]
        )
        report = recorded_call(
            self.store,
            camera_id,
            request.request_id,
            "robotops/calibration/diagnostics.py",
            "investigate",
            {"identity": report_id, "data": inputs.model_dump(mode="json")},
            partial(investigate, report_id, inputs),
        )
        return self.store.save_investigation(report, inputs, request)

    def begin_measurements(self, camera_id: str, request: Mutation) -> OperationReceipt:
        action = getattr(self.sensor, "mount_board", None)
        if not callable(action):
            raise CalibrationError("CONTROLLER_SENSOR_ADAPTER_REQUIRED")
        self._request(camera_id, "begin-measurements", request, {})
        # Once the lifecycle request is durable, mounting this keyed fixture is an
        # idempotent action. Old candidates/reports remain immutable and inspectable.
        receipt = self.store.begin_measurements(camera_id, request)
        action(request.request_id)
        return receipt
