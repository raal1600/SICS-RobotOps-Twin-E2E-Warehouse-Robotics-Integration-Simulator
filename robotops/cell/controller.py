from robotops.domain.models import CellMode, CellState
from robotops.domain.ports import Runtime


class CellController:
    def __init__(self, runtime: Runtime):
        self.runtime = runtime

    def stop(self) -> CellState:
        return self.runtime.set_cell(CellMode.ESTOP_LOGICAL, "LOGICAL_STOP_REQUESTED")

    def fault(self) -> CellState:
        return self.runtime.set_cell(CellMode.FAULTED, "CELL_FAULT_REQUESTED")

    def reset(self) -> CellState:
        self.runtime.set_cell(CellMode.RESETTING, "RESET_REQUESTED")
        # World/journal remain unchanged. A new generation invalidates old plans.
        return self.runtime.set_cell(CellMode.READY, "RESET_REOBSERVATION_REQUIRED")
