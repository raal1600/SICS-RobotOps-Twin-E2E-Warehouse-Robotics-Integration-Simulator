"""Only documented typed boundaries cross runtime/Brain/observation components."""

from pathlib import Path
from typing import Protocol

from robotops.domain.models import (
    ActionPlan,
    CellMode,
    CellState,
    CommandReceipt,
    Fault,
    InventoryLocation,
    PickJob,
    RobotCommand,
    RobotEvent,
    WorldObservation,
    WorldState,
)


class Brain(Protocol):
    def plan(
        self, job: PickJob, observation: WorldObservation, destination: InventoryLocation
    ) -> ActionPlan: ...


class Runtime(Protocol):
    def reset(self) -> WorldState: ...
    def world(self) -> WorldState: ...
    def apply(self, command: RobotCommand, fault: Fault | None = None) -> CommandReceipt: ...
    def journal(self, command_id: str) -> CommandReceipt | None: ...
    def events(self, command_id: str | None = None) -> list[RobotEvent]: ...
    def set_cell(self, mode: CellMode, reason: str) -> CellState: ...
    def capture(self, path: Path) -> Path: ...


class Observer(Protocol):
    def observe(self, world: WorldState, fault: Fault | None = None) -> WorldObservation: ...
