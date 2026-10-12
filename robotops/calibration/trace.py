"""Instrumentation around real Python calls; no invented executed-line animation."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import SerializerFunctionWrapHandler, model_serializer

from robotops.calibration.contracts import Calculation, Record
from robotops.calibration.errors import CalibrationError
from robotops.calibration.lifecycle import CalibrationStore
from robotops.calibration.provenance import source_snapshot, verify_loaded_callable


class ComputationTrace(Record):
    trace_id: str
    run_id: str
    camera_id: str
    request_id: str
    correlation_id: str
    causation_id: str
    started_at_utc: str
    finished_at_utc: str
    classification: Literal["IN_PROCESS_PYTHON"] = "IN_PROCESS_PYTHON"
    path: str
    symbol: str
    inputs: dict[str, object]
    output: dict[str, object] | None
    error: str | None
    rejected_calculation: Calculation | None = None
    source: dict[str, object]
    scope: str = (
        "Actual function call and returned result; lifecycle approval is a separate operation"
    )

    @model_serializer(mode="wrap")
    def retain_prior_trace(  # type: ignore[no-untyped-def]
        self, handler: SerializerFunctionWrapHandler
    ):
        result: dict[str, object] = handler(self)
        if self.rejected_calculation is None:
            result.pop("rejected_calculation", None)
        return result


def result_record_key(trace: ComputationTrace) -> tuple[str, str] | None:
    """Bind source to a record kind AND ID; capture and PnP intentionally share IDs."""
    result = trace.output or {}
    inputs = trace.inputs
    if "captures" in result and inputs.get("capture_prefix"):
        return "runtime-acquisition", str(inputs["capture_prefix"])
    if trace.error:
        capture = inputs.get("capture")
        identity = (
            capture.get("capture_id") if isinstance(capture, dict) else inputs.get("capture_id")
        )
        return ("rejection", str(identity)) if identity else None
    if "capture_id" in result:
        if "quality_id" in result:
            return "measurement-quality", str(result["quality_id"])
        kind = (
            "capture" if "rgb" in result else "surface-detection" if "mask" in result else "sample"
        )
        return kind, str(result["capture_id"])
    identities = result.get("record_ids")
    if (
        trace.symbol == "CalibrationStore.fault_notice"
        and isinstance(identities, list)
        and identities
    ):
        return "simulation-fault", str(identities[0])
    if (
        trace.symbol == "CalibrationStore.reuse_estimate"
        and isinstance(identities, list)
        and identities
    ):
        return "candidate", str(identities[0])
    if "report_id" in result:
        kind = (
            "camera-model-report"
            if "streams" in result
            else "acquisition-report"
            if "ready_to_fit" in result
            else "validation"
        )
        return kind, str(result["report_id"])
    for field, kind in (
        ("investigation_id", "investigation"),
        ("outcome_id", "pick-outcome"),
        ("quality_id", "measurement-quality"),
        ("batch_id", "reference-batch"),
        ("agreement_id", "camera-agreement"),
        ("candidate_id", "candidate"),
        ("plan_id", "capture-plan"),
        ("check_id", "routine-check"),
        ("verification_id", "tool-verification"),
        ("measurement_id", "tool-measurements"),
    ):
        if field in result:
            return kind, str(result[field])
    if inputs.get("record_id"):
        return "runtime-target", str(inputs["record_id"])
    if inputs.get("capture_id"):
        kind = (
            "reference"
            if trace.symbol == "reconstruct"
            else "runtime-point-error"
            if "code" in result
            else "runtime-point"
        )
        return kind, str(inputs["capture_id"])
    return None


def result_record_keys(trace: ComputationTrace) -> tuple[tuple[str, str], ...]:
    """A recorded batch call also supplies each actual capture, without inventing per-image calls."""
    key = result_record_key(trace)
    if key is None:
        return ()
    keys = [key]
    if key[0] in {"reference-batch", "runtime-acquisition"} and trace.output:
        captures = trace.output.get("captures")
        if isinstance(captures, list):
            for item in captures:
                capture = (
                    item.get("capture")
                    if key[0] == "reference-batch" and isinstance(item, dict)
                    else item
                )
                if isinstance(capture, dict) and capture.get("capture_id"):
                    keys.append(("capture", str(capture["capture_id"])))
    return tuple(keys)


def recorded_call[T: Record](
    store: CalibrationStore,
    camera_id: str,
    request_id: str,
    path: str,
    symbol: str,
    inputs: dict[str, object],
    call: Callable[[], T],
) -> T:
    started = datetime.now(UTC).isoformat()
    saved_source = source_snapshot(path, symbol)
    saved_source["scope"] = "Saved file snapshot; loaded function has not been verified."
    saved_source["loaded_function_verification"] = "UNVERIFIED"
    output, error = None, None
    rejected_calculation = None
    try:
        saved_source.update(verify_loaded_callable(saved_source, path, symbol, call))
        result = call()
        output = result.model_dump(mode="json")
        return result
    except Exception as exception:
        error = f"{type(exception).__name__}: {exception}"
        if isinstance(exception, CalibrationError) and exception.calculation is not None:
            rejected_calculation = Calculation.model_validate(exception.calculation)
        raise
    finally:
        trace = ComputationTrace(
            trace_id=str(uuid4()),
            run_id=store.store.run_id,
            camera_id=camera_id,
            request_id=request_id,
            correlation_id=f"{store.store.run_id}:{camera_id}",
            causation_id=request_id,
            started_at_utc=started,
            finished_at_utc=datetime.now(UTC).isoformat(),
            path=path,
            symbol=symbol,
            inputs=inputs,
            output=output,
            error=error,
            rejected_calculation=rejected_calculation,
            source=saved_source,
        )
        with store.store.transaction() as db:
            store._put(db, "calculation-trace", trace.trace_id, trace)
