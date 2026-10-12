"""Publish only typed records declared in the listed public calibration modules."""

from robotops.calibration import (
    acquisition,
    agreement,
    checks,
    contracts,
    diagnostics,
    faults,
    inspection,
    lifecycle,
    optics,
    outcome,
    presentation,
    registration,
    runtime_contracts,
    tcp,
    trace,
)

CALIBRATION_SCHEMAS = tuple(
    sorted(
        (
            value
            for module in (
                contracts,
                diagnostics,
                faults,
                registration,
                runtime_contracts,
                acquisition,
                agreement,
                checks,
                inspection,
                lifecycle,
                optics,
                outcome,
                presentation,
                tcp,
                trace,
            )
            for value in vars(module).values()
            if isinstance(value, type)
            and issubclass(value, contracts.Record)
            and value is not contracts.Record
            and value.__module__ == module.__name__
        ),
        key=lambda model: model.__name__,
    )
)
