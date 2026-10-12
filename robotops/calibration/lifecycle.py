"""Durable calibration lifecycle in the existing application run store.

Only this mutable index chooses an active artifact. Candidates, captures, reports,
approvals and operation receipts are immutable JSON. Inspection uses read-only SQLite
connections; candidate/validation progress never silently changes active validity.
"""

import hashlib
import json
import sqlite3
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Literal

from pydantic import Field

from robotops.calibration.acquisition import AcquisitionReport, CapturePlan, assess
from robotops.calibration.checks import RoutineCheck, evaluate_references
from robotops.calibration.contracts import (
    ApprovalRecord,
    Board,
    CalibrationArtifact,
    Camera,
    Candidate,
    Capture,
    EstimateLineage,
    Id,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PoseSample,
    Record,
    ValidationReport,
)
from robotops.calibration.diagnostics import InvestigationInputs, InvestigationReport, investigate
from robotops.calibration.errors import CalibrationError
from robotops.calibration.faults import FaultRecord
from robotops.calibration.optics import CameraModelReport, OpticalReference, verify_camera_model
from robotops.calibration.tcp import ToolMeasurements, ToolVerification, verify_measurements
from robotops.calibration.validation import validate
from robotops.workflow.store import Conflict, NotFound, Store


class CameraState(Record):
    camera: Camera
    board: Board
    limits: Limits
    revision: int = Field(ge=1)
    active_artifact_id: Id | None = None
    active_validity: Literal["UNVERIFIED", "VERIFIED", "SUSPECT_INVALID"] = "UNVERIFIED"
    workflow_state: Literal[
        "UNVERIFIED",
        "NEW_MEASUREMENTS",
        "CANDIDATE",
        "INDEPENDENT_VALIDATION",
        "APPROVED",
        "REJECTED",
        "INVESTIGATION",
    ] = "UNVERIFIED"
    candidate_id: Id | None = None
    report_id: Id | None = None
    camera_model_report_id: Id | None = None
    blocking_reasons: tuple[str, ...] = ("APPROVED_CALIBRATION_REQUIRED",)


class Mutation(Record):
    request_id: Id
    expected_revision: int = Field(ge=0)


class ValidationReservation(Record):
    reservation_id: Id
    candidate_id: Id
    candidate_fingerprint: str
    dataset_ids: tuple[Id, ...]
    reserved_at_utc: str


class OperationReceipt(Record):
    run_id: str
    operation: str
    request_id: Id
    camera_id: Id
    state: CameraState
    record_ids: tuple[str, ...]
    timestamp_utc: str
    classification: Literal["IN_PROCESS_PYTHON"] = "IN_PROCESS_PYTHON"


def _now() -> str:
    return datetime.now(UTC).isoformat()


class CalibrationStore:
    def __init__(self, store: Store):
        self.store = store
        with store.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS calibration_cameras (
                    id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_records (
                    kind TEXT NOT NULL, id TEXT NOT NULL, fingerprint TEXT NOT NULL, body TEXT NOT NULL,
                    PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS calibration_operations (
                    camera_id TEXT NOT NULL, request_id TEXT NOT NULL, payload_hash TEXT NOT NULL,
                    body TEXT NOT NULL, PRIMARY KEY(camera_id,request_id));
                CREATE TABLE IF NOT EXISTS calibration_holdouts (
                    dataset_id TEXT PRIMARY KEY, candidate_fingerprint TEXT NOT NULL,
                    reservation_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calibration_measurement_use (
                    measurement_hash TEXT PRIMARY KEY, partition TEXT NOT NULL,
                    candidate_fingerprint TEXT NOT NULL);
            """)

    @staticmethod
    def _put(db: sqlite3.Connection, kind: str, identity: str, record: Record) -> None:
        row = db.execute(
            "SELECT fingerprint FROM calibration_records WHERE kind=? AND id=?", (kind, identity)
        ).fetchone()
        if row:
            if row[0] != record.fingerprint():
                raise Conflict("IMMUTABLE_CALIBRATION_RECORD_CONFLICT")
            return
        db.execute(
            "INSERT INTO calibration_records VALUES (?,?,?,?)",
            (kind, identity, record.fingerprint(), record.model_dump_json()),
        )

    @staticmethod
    def _record[T: Record](db: sqlite3.Connection, kind: str, identity: str, schema: type[T]) -> T:
        row = db.execute(
            "SELECT body,fingerprint FROM calibration_records WHERE kind=? AND id=?",
            (kind, identity),
        ).fetchone()
        if row is None:
            raise NotFound(f"CALIBRATION_{kind.upper()}_NOT_FOUND")
        record = schema.model_validate_json(row[0])
        if record.fingerprint() != row[1]:
            raise CalibrationError("CALIBRATION_RECORD_HASH_MISMATCH")
        return record

    def record[T: Record](self, kind: str, identity: str, schema: type[T]) -> T:
        with self.store.readonly_connect() as db:
            return self._record(db, kind, identity, schema)

    def state(self, camera_id: str) -> CameraState:
        with self.store.readonly_connect() as db:
            row = db.execute(
                "SELECT body FROM calibration_cameras WHERE id=?", (camera_id,)
            ).fetchone()
        if row is None:
            raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
        return CameraState.model_validate_json(row[0])

    def states(self) -> list[CameraState]:
        with self.store.readonly_connect() as db:
            return [
                CameraState.model_validate_json(row[0])
                for row in db.execute("SELECT body FROM calibration_cameras ORDER BY id").fetchall()
            ]

    def _mutate(
        self,
        camera_id: str,
        operation: str,
        request: Mutation,
        payload: object,
        apply: Callable[
            [sqlite3.Connection, CameraState | None], tuple[CameraState, tuple[str, ...]]
        ],
    ) -> OperationReceipt:
        request_hash = hashlib.sha256(
            json.dumps(
                {
                    "operation": operation,
                    "request": request.model_dump(mode="json"),
                    "payload": payload,
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
        with self.store.transaction() as db:
            prior = db.execute(
                "SELECT payload_hash,body FROM calibration_operations WHERE camera_id=? AND request_id=?",
                (camera_id, request.request_id),
            ).fetchone()
            if prior:
                if prior[0] != request_hash:
                    raise Conflict("CALIBRATION_IDEMPOTENCY_CONFLICT")
                return OperationReceipt.model_validate_json(prior[1])
            row = db.execute(
                "SELECT body FROM calibration_cameras WHERE id=?", (camera_id,)
            ).fetchone()
            state = CameraState.model_validate_json(row[0]) if row else None
            if (state.revision if state else 0) != request.expected_revision:
                raise Conflict("STALE_CALIBRATION_REVISION")
            changed, identities = apply(db, state)
            changed = CameraState.model_validate(
                {**changed.model_dump(), "revision": request.expected_revision + 1}
            )
            receipt = OperationReceipt(
                run_id=self.store.run_id,
                operation=operation,
                request_id=request.request_id,
                camera_id=camera_id,
                state=changed,
                record_ids=identities,
                timestamp_utc=_now(),
            )
            db.execute(
                "INSERT INTO calibration_cameras VALUES (?,?) ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                (camera_id, changed.model_dump_json()),
            )
            db.execute(
                "INSERT INTO calibration_operations VALUES (?,?,?,?)",
                (camera_id, request.request_id, request_hash, receipt.model_dump_json()),
            )
            return receipt

    def configure(
        self,
        camera: Camera,
        board: Board,
        limits: Limits,
        request: Mutation,
        model_report: CameraModelReport | None = None,
        optical_references: tuple[OpticalReference, ...] = (),
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, previous: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            state = CameraState(camera=camera, board=board, limits=limits, revision=1)
            if previous and previous.active_artifact_id:
                state = state.model_copy(
                    update={
                        "active_artifact_id": previous.active_artifact_id,
                        "active_validity": "SUSPECT_INVALID",
                        "blocking_reasons": ("CONFIGURATION_REQUIRES_VALIDATION",),
                    }
                )
            for kind, record in (("camera", camera), ("board", board), ("limits", limits)):
                self._put(db, kind, record.fingerprint(), record)
            identities: tuple[str, ...] = (
                camera.fingerprint(),
                board.fingerprint(),
                limits.fingerprint(),
            )
            if model_report is not None:
                if (
                    verify_camera_model(
                        camera, optical_references, model_report.limits, model_report.report_id
                    )
                    != model_report
                ):
                    raise CalibrationError("CAMERA_MODEL_REPORT_RECOMPUTATION_MISMATCH")
                for reference in optical_references:
                    self._put(db, "optical-reference", reference.measurement_id, reference)
                self._put(db, "camera-model-report", model_report.report_id, model_report)
                state = state.model_copy(update={"camera_model_report_id": model_report.report_id})
                if not model_report.passed:
                    state = state.model_copy(update={"blocking_reasons": model_report.failures})
                identities += (model_report.report_id,)
            return state, identities

        return self._mutate(
            camera.camera_id,
            "configure",
            request,
            [
                camera.model_dump(mode="json"),
                board.model_dump(mode="json"),
                limits.model_dump(mode="json"),
                model_report.model_dump(mode="json") if model_report else None,
            ],
            apply,
        )

    def require_camera_model(self, state: CameraState) -> CameraModelReport:
        if state.camera_model_report_id is None:
            raise CalibrationError(
                "CAMERA_MODEL_VERIFICATION_REQUIRED",
                "Historical configuration has no saved optical model verification",
            )
        report = self.record("camera-model-report", state.camera_model_report_id, CameraModelReport)
        if (
            not report.passed
            or report.camera_configuration_fingerprint != state.camera.fingerprint()
        ):
            raise CalibrationError("CAMERA_MODEL_NOT_VERIFIED", ", ".join(report.failures))
        return report

    def save_measurements(
        self,
        camera_id: str,
        captures: Sequence[Capture],
        samples: Sequence[PoseSample],
        rejected: Sequence[MeasurementRejection],
        request: Mutation,
        plan: CapturePlan | None = None,
        report: AcquisitionReport | None = None,
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
            capture_map = {c.capture_id: c for c in captures}
            if len(capture_map) != len(captures):
                raise CalibrationError("DUPLICATE_CAPTURE_ID")
            for capture in captures:
                if capture.camera_id != camera_id or capture.partition != "fit":
                    raise CalibrationError("FIT_CAPTURE_SCOPE_MISMATCH")
                if (
                    capture.configuration_fingerprint != state.camera.fingerprint()
                    or capture.board_fingerprint != state.board.fingerprint()
                ):
                    raise CalibrationError("ACQUISITION_CONFIGURATION_CHANGED")
                self._put(db, "capture", capture.capture_id, capture)
            for sample in samples:
                matched_capture = capture_map.get(sample.capture_id)
                if (
                    matched_capture is None
                    or not matched_capture.admitted
                    or sample.partition != "fit"
                ):
                    raise CalibrationError("UNBOUND_FIT_SAMPLE")
                self._put(db, "sample", sample.capture_id, sample)
            for rejection in rejected:
                if rejection.capture_id not in capture_map:
                    raise CalibrationError("UNBOUND_MEASUREMENT_REJECTION")
                self._put(db, "rejection", rejection.capture_id, rejection)
            if (
                {sample.capture_id for sample in samples} | {r.capture_id for r in rejected}
            ) != set(capture_map):
                raise CalibrationError("CAPTURE_DECISION_MISSING")
            if plan is not None or report is not None:
                if (
                    plan is None
                    or report is None
                    or assess(plan, captures, samples, rejected, state.camera, state.limits)
                    != report
                ):
                    raise CalibrationError("ACQUISITION_REPORT_RECOMPUTATION_MISMATCH")
                self._put(db, "capture-plan", plan.plan_id, plan)
                self._put(db, "acquisition-report", report.report_id, report)
            return state.model_copy(update={"workflow_state": "NEW_MEASUREMENTS"}), tuple(
                capture_map
            )

        payload = (
            [c.fingerprint() for c in captures]
            + [s.fingerprint() for s in samples]
            + [r.fingerprint() for r in rejected]
        )
        if plan is not None and report is not None:
            payload += [plan.fingerprint(), report.fingerprint()]
        return self._mutate(camera_id, "acquire", request, payload, apply)

    @staticmethod
    def _use_capture(
        db: sqlite3.Connection, capture: Capture, partition: str, candidate_hash: str
    ) -> None:
        identity = hashlib.sha256(
            (capture.rgb.sha256 + capture.depth.sha256 + capture.t_b_f.fingerprint()).encode()
        ).hexdigest()
        prior = db.execute(
            "SELECT partition,candidate_fingerprint FROM calibration_measurement_use WHERE measurement_hash=?",
            (identity,),
        ).fetchone()
        if prior and (
            prior[0] != partition or (partition == "validation" and prior[1] != candidate_hash)
        ):
            raise CalibrationError("MEASUREMENT_HOLDOUT_REUSE")
        db.execute(
            "INSERT OR IGNORE INTO calibration_measurement_use VALUES (?,?,?)",
            (identity, partition, candidate_hash),
        )

    def save_candidate(self, candidate: Candidate, request: Mutation) -> OperationReceipt:
        if candidate.reused_from is not None:
            raise CalibrationError("REUSE_REQUIRES_IMMUTABLE_APPROVED_ARTIFACT")

        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            state = self._applicable_candidate(candidate, state)
            self.require_camera_model(state)
            for identity in candidate.sample_ids:
                sample = self._record(db, "sample", identity, PoseSample)
                capture = self._record(db, "capture", identity, Capture)
                if sample.partition != "fit" or sample.camera_id != candidate.camera.camera_id:
                    raise CalibrationError("FIT_SAMPLE_SCOPE_MISMATCH")
                self._use_capture(db, capture, "fit", candidate.fingerprint())
            self._put(db, "candidate", candidate.candidate_id, candidate)
            return state.model_copy(
                update={
                    "candidate_id": candidate.candidate_id,
                    "report_id": None,
                    "workflow_state": "CANDIDATE",
                }
            ), (candidate.candidate_id,)

        return self._mutate(
            candidate.camera.camera_id, "fit", request, candidate.model_dump(mode="json"), apply
        )

    def reuse_estimate(
        self, camera_id: str, artifact_id: str, candidate_id: str, request: Mutation
    ) -> OperationReceipt:
        """Copy an immutable approved estimate, never its approval or validation authority."""

        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            original = self._record(db, "artifact", artifact_id, CalibrationArtifact)
            state = self._applicable_candidate(original.candidate, state)
            self.require_camera_model(state)
            if original.candidate.camera.camera_id != camera_id:
                raise CalibrationError("CANDIDATE_CONFIGURATION_NOT_APPLICABLE")
            # Construct from the saved record inside the transaction. The caller cannot
            # substitute matrices, training samples, solver provenance or old approval.
            candidate = Candidate.model_validate(
                {
                    **original.candidate.model_dump(mode="json"),
                    "candidate_id": candidate_id,
                    "reused_from": EstimateLineage(
                        artifact_id=artifact_id,
                        artifact_fingerprint=original.fingerprint(),
                        candidate_fingerprint=original.candidate.fingerprint(),
                        created_at_utc=_now(),
                    ).model_dump(mode="json"),
                }
            )
            self._put(db, "candidate", candidate_id, candidate)
            return state.model_copy(
                update={
                    "candidate_id": candidate_id,
                    "report_id": None,
                    "workflow_state": "CANDIDATE",
                }
            ), (candidate_id,)

        return self._mutate(
            camera_id, "reuse-estimate", request, [artifact_id, candidate_id], apply
        )

    @staticmethod
    def _applicable_candidate(candidate: Candidate, state: CameraState | None) -> CameraState:
        if state is None:
            raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
        if (
            candidate.camera.fingerprint() != state.camera.fingerprint()
            or candidate.board.fingerprint() != state.board.fingerprint()
            or candidate.limits_fingerprint != state.limits.fingerprint()
        ):
            raise CalibrationError("CANDIDATE_CONFIGURATION_NOT_APPLICABLE")
        return state

    def reserve_validation(
        self, camera_id: str, candidate_id: str, dataset_ids: tuple[str, ...], request: Mutation
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            candidate = self._record(db, "candidate", candidate_id, Candidate)
            state = self._applicable_candidate(candidate, state)
            if (
                state.candidate_id != candidate_id
                or not dataset_ids
                or set(dataset_ids) & set(candidate.dataset_ids)
            ):
                raise CalibrationError("VALIDATION_CANDIDATE_OR_DATASET_MISMATCH")
            reservation = ValidationReservation(
                reservation_id=request.request_id,
                candidate_id=candidate_id,
                candidate_fingerprint=candidate.fingerprint(),
                dataset_ids=dataset_ids,
                reserved_at_utc=_now(),
            )
            for dataset in dataset_ids:
                if db.execute(
                    "SELECT 1 FROM calibration_holdouts WHERE dataset_id=?", (dataset,)
                ).fetchone():
                    raise CalibrationError("FINAL_VALIDATION_DATASET_ALREADY_USED")
                db.execute(
                    "INSERT INTO calibration_holdouts VALUES (?,?,?)",
                    (dataset, candidate.fingerprint(), reservation.reservation_id),
                )
            self._put(db, "validation-reservation", reservation.reservation_id, reservation)
            return state.model_copy(update={"workflow_state": "INDEPENDENT_VALIDATION"}), (
                reservation.reservation_id,
            )

        return self._mutate(
            camera_id, "reserve-validation", request, [candidate_id, dataset_ids], apply
        )

    def save_validation(
        self,
        camera_id: str,
        reservation_id: str,
        report: ValidationReport,
        captures: Sequence[Capture],
        samples: Sequence[PoseSample],
        references: Sequence[IndependentReference],
        request: Mutation,
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            candidate = self._record(db, "candidate", report.candidate_id, Candidate)
            state = self._applicable_candidate(candidate, state)
            reservation = self._record(
                db, "validation-reservation", reservation_id, ValidationReservation
            )
            if (
                reservation.candidate_fingerprint != report.candidate_fingerprint
                or report.candidate_fingerprint != candidate.fingerprint()
                or set(report.dataset_ids) != set(reservation.dataset_ids)
            ):
                raise CalibrationError("UNRESERVED_VALIDATION_REPORT")
            independently_checked = validate(
                candidate,
                samples,
                references,
                state.limits,
                report.report_id,
                report.rejected_measurements,
            )
            if independently_checked.fingerprint() != report.fingerprint():
                raise CalibrationError("VALIDATION_REPORT_DOES_NOT_MATCH_MEASUREMENTS")
            capture_ids = {capture.capture_id for capture in captures}
            for capture in captures:
                if (
                    capture.partition != "validation"
                    or capture.camera_id != camera_id
                    or capture.dataset_id not in reservation.dataset_ids
                ):
                    raise CalibrationError("VALIDATION_CAPTURE_SCOPE_MISMATCH")
                self._use_capture(db, capture, "validation", candidate.fingerprint())
                self._put(db, "capture", capture.capture_id, capture)
            for sample in samples:
                if sample.capture_id not in capture_ids:
                    raise CalibrationError("UNBOUND_VALIDATION_SAMPLE")
                self._put(db, "sample", sample.capture_id, sample)
            for reference in references:
                if reference.reference_id not in capture_ids:
                    raise CalibrationError("UNBOUND_REFERENCE_MEASUREMENT")
                self._put(db, "reference", reference.reference_id, reference)
            for rejection in report.rejected_measurements:
                if rejection.capture_id not in capture_ids:
                    raise CalibrationError("UNBOUND_VALIDATION_REJECTION")
                self._put(db, "rejection", rejection.capture_id, rejection)
            self._put(db, "validation", report.report_id, report)
            return state.model_copy(
                update={
                    "report_id": report.report_id,
                    "workflow_state": "INDEPENDENT_VALIDATION" if report.passed else "REJECTED",
                }
            ), (report.report_id,)

        payload = [
            reservation_id,
            report.fingerprint(),
            [c.fingerprint() for c in captures],
            [s.fingerprint() for s in samples],
            [r.fingerprint() for r in references],
        ]
        return self._mutate(camera_id, "validate", request, payload, apply)

    def approve(
        self, camera_id: str, candidate_id: str, report_id: str, actor: str, request: Mutation
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            candidate = self._record(db, "candidate", candidate_id, Candidate)
            report = self._record(db, "validation", report_id, ValidationReport)
            state = self._applicable_candidate(candidate, state)
            optical_report = self.require_camera_model(state)
            if (
                state.candidate_id != candidate_id
                or state.report_id != report_id
                or state.workflow_state != "INDEPENDENT_VALIDATION"
            ):
                raise CalibrationError("CURRENT_CANDIDATE_VALIDATION_REQUIRED")
            if not report.passed:
                raise CalibrationError("PASSING_INDEPENDENT_VALIDATION_REQUIRED")
            approval = ApprovalRecord(
                actor=actor,
                timestamp_utc=_now(),
                candidate_fingerprint=candidate.fingerprint(),
                report_fingerprint=report.fingerprint(),
            )
            artifact = CalibrationArtifact(
                artifact_id=f"approved-{candidate_id}",
                candidate=candidate,
                validation=report,
                approval=approval,
                camera_model_report_id=optical_report.report_id,
                camera_model_report_fingerprint=optical_report.fingerprint(),
            )
            self._put(db, "artifact", artifact.artifact_id, artifact)
            return state.model_copy(
                update={
                    "active_artifact_id": artifact.artifact_id,
                    "active_validity": "VERIFIED",
                    "workflow_state": "APPROVED",
                    "blocking_reasons": (),
                }
            ), (artifact.artifact_id,)

        return self._mutate(camera_id, "approve", request, [candidate_id, report_id, actor], apply)

    def invalidate(self, camera_id: str, reason: str, request: Mutation) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
            return state.model_copy(
                update={
                    "active_validity": "SUSPECT_INVALID",
                    "workflow_state": "INVESTIGATION",
                    "blocking_reasons": (reason,),
                }
            ), ()

        if not reason.strip():
            raise CalibrationError("INVALIDATION_REASON_REQUIRED")
        return self._mutate(camera_id, "invalidate", request, reason, apply)

    def active(self, camera_id: str) -> CalibrationArtifact:
        try:
            state = self.state(camera_id)
        except NotFound:
            raise CalibrationError("CALIBRATION_CAMERA_UNCONFIGURED") from None
        if state.active_artifact_id is None:
            raise CalibrationError("APPROVED_CALIBRATION_REQUIRED")
        if state.active_validity != "VERIFIED":
            raise CalibrationError("ACTIVE_CALIBRATION_SUSPECT", ", ".join(state.blocking_reasons))
        optical_report = self.require_camera_model(state)
        artifact = self.record("artifact", state.active_artifact_id, CalibrationArtifact)
        if (
            artifact.camera_model_report_id != optical_report.report_id
            or artifact.camera_model_report_fingerprint != optical_report.fingerprint()
        ):
            raise CalibrationError("APPROVED_OPTICAL_REPORT_BINDING_CHANGED")
        self._applicable_candidate(artifact.candidate, state)
        return artifact

    def save_tool_check(
        self,
        camera_id: str,
        report: ToolVerification,
        request: Mutation,
        measurements: ToolMeasurements,
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
            if state.active_validity != "VERIFIED" or state.active_artifact_id is None:
                raise CalibrationError("APPROVED_CALIBRATION_REQUIRED")
            if verify_measurements(measurements) != report:
                raise CalibrationError("TOOL_REPORT_RECOMPUTATION_MISMATCH")
            self._put(db, "tool-measurements", measurements.measurement_id, measurements)
            self._put(db, "tool-verification", report.verification_id, report)
            return state, (report.verification_id,)

        return self._mutate(
            camera_id,
            "verify-tool",
            request,
            {"report": report.model_dump(mode="json"), "measurements": measurements.fingerprint()},
            apply,
        )

    def save_routine_check(
        self, report: RoutineCheck, request: Mutation, references: tuple[IndependentReference, ...]
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None or state.active_artifact_id != report.artifact_id:
                raise CalibrationError("ROUTINE_CHECK_ARTIFACT_CHANGED")
            if (
                evaluate_references(
                    report.check_id,
                    report.camera_id,
                    report.artifact_id,
                    references,
                    report.failed_capture_ids,
                    state.limits,
                )
                != report
            ):
                raise CalibrationError("ROUTINE_REPORT_RECOMPUTATION_MISMATCH")
            for reference in references:
                if (
                    self._record(db, "reference", reference.reference_id, IndependentReference)
                    != reference
                ):
                    raise CalibrationError("ROUTINE_REFERENCE_NOT_SAVED")
                capture = self._record(db, "capture", reference.reference_id, Capture)
                if (
                    capture.partition != "routine"
                    or capture.camera_id != report.camera_id
                    or capture.configuration_fingerprint != state.camera.fingerprint()
                ):
                    raise CalibrationError("ROUTINE_REFERENCE_SCOPE_MISMATCH")
            for identity in report.failed_capture_ids:
                capture = self._record(db, "capture", identity, Capture)
                self._record(db, "rejection", identity, MeasurementRejection)
                if capture.partition != "routine" or capture.camera_id != report.camera_id:
                    raise CalibrationError("ROUTINE_REJECTION_SCOPE_MISMATCH")
            self._put(db, "routine-check", report.check_id, report)
            if not report.passed:
                state = state.model_copy(
                    update={
                        "active_validity": "SUSPECT_INVALID",
                        "workflow_state": "INVESTIGATION",
                        "blocking_reasons": report.failures,
                    }
                )
            # Passing routine data cannot approve/restore an already suspect artifact.
            return state, (report.check_id,)

        return self._mutate(
            report.camera_id, "routine-check", request, report.model_dump(mode="json"), apply
        )

    def save_investigation(
        self, report: InvestigationReport, inputs: InvestigationInputs, request: Mutation
    ) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
            if (
                report.camera_id != state.camera.camera_id
                or investigate(report.investigation_id, inputs) != report
            ):
                raise CalibrationError("INVESTIGATION_REPORT_RECOMPUTATION_MISMATCH")
            row = db.execute(
                "SELECT fingerprint FROM calibration_records WHERE kind=? AND id=?",
                (inputs.source_kind, inputs.source_id),
            ).fetchone()
            if row is None or row[0] != inputs.source_fingerprint:
                raise CalibrationError("INVESTIGATION_SOURCE_BINDING_MISMATCH")
            for sample in inputs.samples:
                if self._record(db, "sample", sample.capture_id, PoseSample) != sample:
                    raise CalibrationError("INVESTIGATION_SAMPLE_NOT_SAVED")
            for reference in inputs.references:
                if (
                    self._record(db, "reference", reference.reference_id, IndependentReference)
                    != reference
                ):
                    raise CalibrationError("INVESTIGATION_REFERENCE_NOT_SAVED")
            for rejection in inputs.rejections:
                if (
                    self._record(db, "rejection", rejection.capture_id, MeasurementRejection)
                    != rejection
                ):
                    raise CalibrationError("INVESTIGATION_REJECTION_NOT_SAVED")
            if (
                inputs.previous_routine is not None
                and self._record(
                    db, "routine-check", inputs.previous_routine.check_id, RoutineCheck
                )
                != inputs.previous_routine
            ):
                raise CalibrationError("INVESTIGATION_PREVIOUS_CHECK_NOT_SAVED")
            self._put(db, "investigation-input", report.investigation_id, inputs)
            self._put(db, "investigation", report.investigation_id, report)
            return state, (report.investigation_id,)

        return self._mutate(report.camera_id, "investigate", request, inputs.fingerprint(), apply)

    def begin_measurements(self, camera_id: str, request: Mutation) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise CalibrationError("CALIBRATION_CAMERA_UNCONFIGURED")
            return state.model_copy(
                update={"workflow_state": "UNVERIFIED", "candidate_id": None, "report_id": None}
            ), ()

        return self._mutate(camera_id, "begin-measurements", request, None, apply)

    def fault_notice(self, fault: FaultRecord, request: Mutation) -> OperationReceipt:
        def apply(
            db: sqlite3.Connection, state: CameraState | None
        ) -> tuple[CameraState, tuple[str, ...]]:
            if state is None:
                raise NotFound("CALIBRATION_CAMERA_NOT_CONFIGURED")
            self._put(db, "simulation-fault", fault.fault_id, fault)
            if fault.definition.affected == "limits":
                limits = (
                    Limits()
                    if fault.definition.kind == "restore_limits"
                    else state.limits.model_copy(
                        update={
                            "limits_id": fault.fault_id,
                            "max_reference_error_mm": None,
                        }
                    )
                )
                state = state.model_copy(
                    update={
                        "limits": limits,
                        "active_validity": "SUSPECT_INVALID",
                        "workflow_state": "INVESTIGATION",
                        "blocking_reasons": (
                            "LIMITS_CHANGED_REQUIRES_INDEPENDENT_VALIDATION"
                            if fault.definition.kind == "restore_limits"
                            else "MISSING_REFERENCE_LIMIT",
                        ),
                    }
                )
            if fault.definition.affected == "board":
                # One shared physical fixture. Invalidate all configured cameras in
                # this same transaction before the sensor adapter changes the board.
                # A concurrent fit/approval uses its old revision and cannot commit.
                updates = {
                    "active_validity": "SUSPECT_INVALID",
                    "workflow_state": "INVESTIGATION",
                    "blocking_reasons": ("SHARED_BOARD_CHANGED_REQUIRES_NEW_MEASUREMENTS",),
                }
                for row in db.execute("SELECT id,body FROM calibration_cameras").fetchall():
                    if row[0] == fault.camera_id:
                        continue
                    other = CameraState.model_validate_json(row[1])
                    changed = other.model_copy(update={**updates, "revision": other.revision + 1})
                    db.execute(
                        "UPDATE calibration_cameras SET body=? WHERE id=?",
                        (changed.model_dump_json(), row[0]),
                    )
                state = state.model_copy(update=updates)
            if fault.definition.affected in {"sensor", "configuration"}:
                state = state.model_copy(
                    update={
                        "active_validity": "SUSPECT_INVALID",
                        "workflow_state": "INVESTIGATION",
                        "blocking_reasons": (
                            "KNOWN_SENSOR_OUTPUT_CHANGE_REQUIRES_INDEPENDENT_CHECKS",
                        ),
                    }
                )
            return state, (fault.fault_id,)

        return self._mutate(
            fault.camera_id, "simulation-fault", request, fault.model_dump(mode="json"), apply
        )
