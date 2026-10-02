"""Deterministic scenario runner. Oracle checks belong to this test/demo harness only."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.domain.models import Fault, JobState, OrderLine, OrderRequest, new_id
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def make_engine(directory: Path, runtime_mode: str = "headless") -> Engine:
    runtime = (BlenderRuntime if runtime_mode == "blender" else SyntheticRuntime)(
        directory / "runtime.db"
    )
    return Engine(Store(directory / "workflow.db"), runtime)


def run_demo(directory: Path, scenario: str, runtime_mode: str = "headless") -> dict[str, Any]:
    if (directory / "workflow.db").exists():
        raise ValueError("Demo needs a new directory; existing evidence is never overwritten.")
    engine = make_engine(directory, runtime_mode)
    order = engine.store.intake(
        OrderRequest(
            order_id="demo-order",
            lines=(
                OrderLine(
                    order_line_id="demo-line",
                    product_id="product-red",
                    source_id="source",
                    destination_id="destination",
                ),
            ),
        ),
        "demo-idempotency-key",
    )
    fault = {
        "happy_path": None,
        "lost_ack_after_effect": Fault.DROP_ACK_AFTER_EFFECT,
        "lost_ack_before_effect": Fault.DROP_ACK_BEFORE_EFFECT,
        "ambiguous": Fault.DROP_ACK_AFTER_EFFECT,
        "restart": Fault.DROP_ACK_AFTER_EFFECT,
        "logical_estop": Fault.LOGICAL_ESTOP,
        "cell_fault": Fault.CELL_FAULT,
    }[scenario]
    job = engine.run(order.job_ids[0], fault)
    initial = job.state
    if scenario == "restart":
        subprocess.run(
            [
                sys.executable,
                "-m",
                "robotops.demo",
                "--resume",
                "--directory",
                str(directory),
                "--runtime",
                runtime_mode,
            ],
            check=True,
        )
        engine = make_engine(directory, runtime_mode)
        job = engine.store.job(job.job_id)
    elif job.state == JobState.UNKNOWN_OUTCOME:
        job = engine.reconcile(
            job.job_id, Fault.CONTRADICTORY_OBSERVATION if scenario == "ambiguous" else None
        )
    effect_count = sum(event.event_type == "PICK_EFFECT" for event in engine.runtime.events())
    expected_count = (
        0 if scenario in {"lost_ack_before_effect", "logical_estop", "cell_fault"} else 1
    )
    expected_state = (
        JobState.REQUIRES_INTERVENTION
        if scenario == "ambiguous"
        else (JobState.FAILED if expected_count == 0 else JobState.COMPLETED)
    )
    if job.state != expected_state or effect_count != expected_count:
        raise AssertionError(f"SCENARIO_FAILED:{job.state}:{effect_count}")
    timeline = engine.store.timeline(order.order_id)
    result = dict(
        scenario=scenario,
        runtime=runtime_mode,
        initial_state=initial,
        final_state=job.state,
        command_id=job.command_id,
        pick_effect_count=effect_count,
        duplicate_physical_picks=max(0, effect_count - 1),
        order=engine.store.order(order.order_id).model_dump(mode="json"),
        timeline=[event.model_dump(mode="json") for event in timeline],
        controller_events=[event.model_dump(mode="json") for event in engine.runtime.events()],
        oracle_world=engine.runtime.world().model_dump(mode="json"),
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario",
        default="happy_path",
        choices=[
            "happy_path",
            "lost_ack_after_effect",
            "lost_ack_before_effect",
            "ambiguous",
            "restart",
            "logical_estop",
            "cell_fault",
        ],
    )
    parser.add_argument("--directory", type=Path, default=None)
    parser.add_argument("--runtime", choices=["headless", "blender"], default="headless")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    directory = args.directory or Path("runs") / new_id()
    if args.resume:
        recovered = make_engine(directory, args.runtime).recover()
        print(json.dumps({"recovered": [job.state for job in recovered]}))
        return
    result = run_demo(directory, args.scenario, args.runtime)
    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "scenario",
                    "initial_state",
                    "final_state",
                    "command_id",
                    "pick_effect_count",
                    "duplicate_physical_picks",
                ]
            },
            indent=2,
        )
    )
    print("Evidence: " + str((directory / "result.json").resolve()))


if __name__ == "__main__":
    main()
