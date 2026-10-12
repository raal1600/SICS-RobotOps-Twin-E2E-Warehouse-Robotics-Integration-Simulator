"""Bind a measured pick's original command, journal and fresh verification for review."""

from robotops.calibration.contracts import Id, Record
from robotops.calibration.errors import CalibrationError
from robotops.domain.models import (
    CommandReceipt,
    RobotCommand,
    VerificationResult,
    WorldObservation,
)
from robotops.workflow.store import digest


class PickOutcome(Record):
    outcome_id: Id
    camera_id: Id
    artifact_id: Id
    command: RobotCommand
    receipt: CommandReceipt | None
    observation: WorldObservation
    verification: VerificationResult
    scope: str = (
        "Original command and measured post-action result. Failed transfer is a symptom, "
        "not proof that camera X is wrong. Instructor fault labels are excluded from this record."
    )


def summarize_pick(
    command: RobotCommand,
    receipt: CommandReceipt | None,
    observation: WorldObservation,
    verification: VerificationResult,
) -> PickOutcome:
    intent = command.calibrated_plan
    if (
        intent is None
        or observation.schema_version != "3.0"
        or verification.command_id != command.command_id
        or verification.job_id != command.job_id
        or verification.observation_id != observation.observation_id
        or observation.scene_epoch != command.scene_epoch
    ):
        raise CalibrationError("PICK_OUTCOME_IDENTITY_MISMATCH")
    if receipt is not None and (
        receipt.command_id != command.command_id
        or receipt.job_id != command.job_id
        or receipt.payload_hash != digest(command)
    ):
        raise CalibrationError("PICK_OUTCOME_JOURNAL_MISMATCH")
    return PickOutcome(
        outcome_id="pick-" + verification.verification_id,
        camera_id=intent.observed_object.binding.camera_id,
        artifact_id=intent.observed_object.binding.artifact_id,
        command=command,
        receipt=receipt,
        observation=observation,
        verification=verification,
    )
