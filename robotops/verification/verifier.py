from datetime import datetime
from math import dist

from robotops.config import Settings
from robotops.domain.models import (
    CommandReceipt,
    CommandStatus,
    RobotCommand,
    Verdict,
    VerificationResult,
    WorldObservation,
    new_id,
    utc_now,
)
from robotops.observation.quality import quality
from robotops.workflow.store import digest, metadata


class Verifier:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def verify(
        self,
        command: RobotCommand,
        observation: WorldObservation,
        receipt: CommandReceipt | None,
        *,
        now: datetime | None = None,
    ) -> VerificationResult:
        # This runtime type check also rejects WorldState supplied by an untyped caller.
        if not isinstance(observation, WorldObservation):
            raise TypeError("WORLD_OBSERVATION_REQUIRED")
        now = now or utc_now()
        reason = quality(observation, command.product_id, self.settings, now)
        verdict = Verdict.INCONCLUSIVE
        if reason is None:
            if observation.scene_epoch != command.scene_epoch:
                reason = "SCENE_EPOCH_MISMATCH"
            elif not {command.source_id, command.destination_id}.issubset(
                observation.covered_locations
            ):
                reason = "INSUFFICIENT_COVERAGE"
            elif receipt is None or not receipt.journal_durable:
                reason = "JOURNAL_UNAVAILABLE"
            elif (
                receipt.command_id != command.command_id
                or receipt.job_id != command.job_id
                or receipt.scene_epoch != command.scene_epoch
                or receipt.payload_hash != digest(command)
            ):
                reason = "JOURNAL_IDENTITY_MISMATCH"
            elif observation.captured_at < max(command.timestamp, receipt.timestamp):
                reason = "OBSERVATION_PRECEDES_EFFECT_EVIDENCE"
            else:
                obj = next(
                    obj for obj in observation.objects if obj.product_id == command.product_id
                )
                if (
                    receipt.status == CommandStatus.SUCCEEDED
                    and receipt.effect_count == 1
                    and obj.location_id == command.destination_id
                    and dist(obj.pose.position, command.target_pose.position)
                    <= self.settings.pose_tolerance_m + obj.uncertainty_m
                ):
                    verdict = Verdict.VERIFIED_SUCCESS
                    reason = "JOURNAL_AND_FRESH_DESTINATION_AGREE"
                elif (
                    receipt.status in {CommandStatus.REJECTED, CommandStatus.FAILED}
                    and receipt.effect_count == 0
                    and obj.location_id == command.source_id
                ):
                    verdict = Verdict.VERIFIED_FAILURE
                    reason = "JOURNAL_AND_FRESH_SOURCE_PROVE_NO_EFFECT"
                else:
                    reason = "JOURNAL_OBSERVATION_CONFLICT_OR_INCOMPLETE"
        return VerificationResult(
            **metadata(command, observation.observation_id, now),
            verification_id=new_id(),
            job_id=command.job_id,
            command_id=command.command_id,
            observation_id=observation.observation_id,
            verdict=verdict,
            reason=reason,
        )
