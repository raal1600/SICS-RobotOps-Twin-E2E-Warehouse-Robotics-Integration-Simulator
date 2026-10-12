"""Assemble diagnostic inputs from scoped saved evidence, never instructor fault labels."""

import json

from robotops.calibration.acquisition import AcquisitionReport
from robotops.calibration.checks import RoutineCheck
from robotops.calibration.contracts import (
    CalibrationArtifact,
    Candidate,
    Capture,
    IndependentReference,
    Limits,
    MeasurementRejection,
    PointFailure,
    PoseSample,
    Record,
    ValidationReport,
)
from robotops.calibration.diagnostics import InvestigationInputs, InvestigationKind
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore, OperationReceipt
from robotops.calibration.outcome import PickOutcome
from robotops.calibration.tcp import ToolVerification
from robotops.calibration.trace import ComputationTrace


def limits_evidence(store: CalibrationStore, camera_id: str, fingerprint: str) -> Limits:
    state = store.state(camera_id)
    if state.limits.fingerprint() == fingerprint:
        return state.limits
    with store.store.readonly_connect() as db:
        rows = db.execute(
            "SELECT body FROM calibration_operations WHERE camera_id=? ORDER BY rowid DESC",
            (camera_id,),
        ).fetchall()
    for row in rows:
        limits = OperationReceipt.model_validate_json(row[0]).state.limits
        if limits.fingerprint() == fingerprint:
            return limits
    raise CalibrationError("INVESTIGATION_SAVED_LIMITS_REQUIRED")


def saved_inputs(
    store: CalibrationStore, camera_id: str, kind: InvestigationKind, identity: str
) -> InvestigationInputs:
    state = store.state(camera_id)
    camera, limits = state.camera, state.limits
    values: dict[str, object] = {}
    record: Record
    if kind == "validation":
        record = store.record(kind, identity, ValidationReport)
        candidate = store.record("candidate", record.candidate_id, Candidate)
        camera = candidate.camera
        limits = limits_evidence(store, camera_id, record.limits_fingerprint)
        values.update(
            validation=record,
            samples=tuple(
                store.record("sample", item.capture_id, PoseSample) for item in record.images
            ),
            references=tuple(
                store.record("reference", item.reference_id, IndependentReference)
                for item in record.references
            ),
            rejections=record.rejected_measurements,
        )
    elif kind == "routine-check":
        record = store.record(kind, identity, RoutineCheck)
        artifact = store.record("artifact", record.artifact_id, CalibrationArtifact)
        camera = artifact.candidate.camera
        with store.store.readonly_connect() as db:
            trace_ids = db.execute(
                "SELECT id FROM calibration_records WHERE kind='calculation-trace' ORDER BY rowid DESC"
            ).fetchall()
        for trace_row in trace_ids:
            call = store.record("calculation-trace", trace_row[0], ComputationTrace)
            if (
                call.symbol == "evaluate_references"
                and call.output
                and call.output.get("check_id") == identity
            ):
                limits = Limits.model_validate(call.inputs["limits"])
                break
        else:
            raise CalibrationError("INVESTIGATION_ROUTINE_LIMITS_EVIDENCE_REQUIRED")
        previous = None
        with store.store.readonly_connect() as db:
            rows = db.execute(
                "SELECT id,body FROM calibration_records WHERE kind='routine-check' AND rowid < (SELECT rowid FROM calibration_records WHERE kind='routine-check' AND id=?) ORDER BY rowid DESC",
                (identity,),
            ).fetchall()
        for row in rows:
            body = json.loads(row[1])
            if body["camera_id"] == camera_id and body["artifact_id"] == record.artifact_id:
                previous = store.record(kind, row[0], RoutineCheck)
                break
        values.update(
            routine=record,
            previous_routine=previous,
            references=tuple(
                store.record("reference", item.reference_id, IndependentReference)
                for item in record.references
            ),
            rejections=tuple(
                store.record("rejection", item, MeasurementRejection)
                for item in record.failed_capture_ids
            ),
        )
    elif kind == "acquisition-report":
        record = store.record(kind, identity, AcquisitionReport)
        if record.camera_id != camera_id:
            raise CalibrationError("INVESTIGATION_CAMERA_MISMATCH")
        limits = limits_evidence(store, camera_id, record.limits_fingerprint)
        values.update(
            acquisition=record,
            rejections=record.rejections,
            samples=tuple(
                store.record("sample", item, PoseSample) for item in record.accepted_capture_ids
            ),
        )
    elif kind == "pick-outcome":
        record = store.record(kind, identity, PickOutcome)
        artifact = store.record("artifact", record.artifact_id, CalibrationArtifact)
        camera = artifact.candidate.camera
        limits = limits_evidence(store, camera_id, artifact.candidate.limits_fingerprint)
        values["pick_outcome"] = record
    elif kind == "tool-verification":
        record = store.record(kind, identity, ToolVerification)
        values["tool"] = record
    elif kind == "rejection":
        record = store.record(kind, identity, MeasurementRejection)
        capture = store.record("capture", identity, Capture)
        if capture.camera_id != camera_id:
            raise CalibrationError("INVESTIGATION_CAMERA_MISMATCH")
        values["rejections"] = (record,)
    else:
        record = store.record(kind, identity, PointFailure)
        if record.camera_id != camera_id:
            raise CalibrationError("INVESTIGATION_CAMERA_MISMATCH")
        values["point_error"] = record
    if camera.camera_id != camera_id:
        raise CalibrationError("INVESTIGATION_CAMERA_MISMATCH")
    return InvestigationInputs.model_validate(
        {
            "camera": camera,
            "limits": limits,
            "source_kind": kind,
            "source_id": identity,
            "source_fingerprint": record.fingerprint(),
            **values,
        }
    )
