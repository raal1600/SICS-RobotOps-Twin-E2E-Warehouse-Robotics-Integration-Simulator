from time import monotonic

from robotops.domain.models import CommandReceipt, Fault, RobotCommand
from robotops.domain.ports import Runtime
from robotops.workflow.store import Store


class RobotGateway:
    def __init__(self, runtime: Runtime, store: Store):
        self.runtime = runtime
        self.store = store

    def send(self, command: RobotCommand, fault: Fault | None = None) -> CommandReceipt:
        original = self.store.load(RobotCommand, command.command_id)
        if original != command:
            raise ValueError("COMMAND_DIFFERS_FROM_DURABLE_INTENT")
        job = self.store.job(command.job_id)
        self.store.emit(job, "gateway", "COMMAND_DISPATCHED", "ORIGINAL_COMMAND_IDENTITY")
        start = monotonic()
        try:
            receipt = self.runtime.apply(command, fault)
        except (TimeoutError, OSError) as exc:
            self.store.emit(
                job,
                "gateway",
                "COMMAND_STATUS_UNKNOWN",
                type(exc).__name__,
                duration_ms=(monotonic() - start) * 1000,
            )
            raise
        finally:
            self.sync_events(command.command_id)
        self.store.emit(
            job,
            "gateway",
            "COMMAND_RECEIPT",
            receipt.status.value,
            duration_ms=(monotonic() - start) * 1000,
        )
        return receipt

    def query(self, command: RobotCommand) -> CommandReceipt | None:
        self.sync_events(command.command_id)
        self.store.emit(
            self.store.job(command.job_id),
            "gateway",
            "JOURNAL_QUERIED",
            "ORIGINAL_COMMAND_IDENTITY",
            evidence_ids=(command.command_id,),
        )
        receipt = self.runtime.journal(command.command_id)
        self.sync_events(command.command_id)
        return receipt

    def sync_events(self, command_id: str | None = None) -> None:
        for event in self.runtime.events(command_id):
            self.store.ingest_robot_event(event)
