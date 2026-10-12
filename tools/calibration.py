"""Run the same measured calibration operations as the application service.

All operations use the same controller-backed service as the application. A guided
pick requires the explicit simulated-execution flag; calibration approval is separate.
"""

import argparse
import json
from pathlib import Path
from typing import get_args

from robotops.calibration.acquisition import CaptureScenario
from robotops.calibration.diagnostics import InvestigationKind
from robotops.calibration.errors import CalibrationError
from robotops.calibration.faults import catalogue
from robotops.calibration.lifecycle import Mutation
from robotops.calibration.reproduction import reproduce
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.domain.models import OrderLine, OrderRequest
from robotops.integration.engine import GuidedEngine
from robotops.integration.models import AuthorizeStage, CreateSession
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Image-driven synthetic calibration; no industrial hardware or RL"
    )
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument(
        "--command-mode",
        choices=["tcp", "flange"],
        help="Controller reference for a newly created world; saved worlds retain their mode",
    )
    parser.add_argument("--camera", choices=["camera-west", "camera-east"], default="camera-west")
    parser.add_argument("--request-id", default="cli-action")
    parser.add_argument("--expected-revision", type=int)
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("configure")
    investigation = commands.add_parser("investigate")
    investigation.add_argument("--kind", required=True, choices=get_args(InvestigationKind))
    investigation.add_argument("--identity", required=True)
    acquire = commands.add_parser("capture")
    acquire.add_argument("--dataset", required=True)
    acquire.add_argument("--repeated-poses", action="store_true")
    acquire.add_argument("--scenario", choices=get_args(CaptureScenario), default="varied")
    fitter = commands.add_parser("fit")
    fitter.add_argument("--dataset", required=True)
    fitter.add_argument("--candidate", required=True)
    reuse = commands.add_parser("reuse-estimate")
    reuse.add_argument("--artifact", required=True)
    reuse.add_argument("--candidate", required=True)
    validator = commands.add_parser("validate")
    validator.add_argument("--candidate", required=True)
    validator.add_argument(
        "--dataset",
        required=True,
        help="Unused final holdout identity; reserved before measurements",
    )
    approve = commands.add_parser("approve")
    approve.add_argument("--candidate", required=True)
    approve.add_argument("--report", required=True)
    approve.add_argument("--actor", required=True)
    commands.add_parser("status")
    replay = commands.add_parser("reproduce")
    replay.add_argument("--bundle", type=Path, required=True)
    for name in ("tool-check", "routine-check", "begin-measurements", "move-camera"):
        commands.add_parser(name)
    fault = commands.add_parser("fault")
    fault.add_argument("--kind", required=True, choices=[item.kind for item in catalogue()])
    pick = commands.add_parser("pick")
    pick.add_argument("--authorize-simulated-execution", action="store_true", required=True)
    demo = commands.add_parser("demonstrate")
    demo.add_argument("--actor", required=True)
    demo.add_argument("--approve-simulation", action="store_true", required=True)
    demo.add_argument("--authorize-simulated-execution", action="store_true", required=True)
    export = commands.add_parser("export")
    export.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory; existing evidence is never replaced",
    )
    args = parser.parse_args()
    if args.operation == "reproduce":
        reproduced = reproduce(args.bundle)
        print(json.dumps(reproduced, indent=2))
        raise SystemExit(0 if reproduced["passed"] else 2)
    if args.run_dir is None:
        parser.error("--run-dir is required for this operation")
    if (
        args.operation not in ("configure", "demonstrate")
        and not (args.run_dir / "workflow.db").is_file()
    ):
        parser.error(
            "Existing --run-dir with workflow.db required; use configure to create a world"
        )
    if args.operation == "demonstrate" and (args.run_dir / "workflow.db").exists():
        parser.error("demonstrate requires a fresh --run-dir; existing evidence is never replaced")
    store = Store(args.run_dir / "workflow.db")
    engine = Engine(
        store,
        SyntheticRuntime(
            args.run_dir / "runtime.db",
            Settings.calibration(seed=args.seed, calibration_command_mode=args.command_mode),
        ),
    )
    service = engine.calibration
    assert service is not None
    if args.operation == "status":
        print(
            json.dumps(
                [state.model_dump(mode="json") for state in service.store.states()], indent=2
            )
        )
        return
    if args.operation == "export":
        print(service.export(args.output).resolve())
        return
    if args.operation == "demonstrate":
        for camera in ("camera-west", "camera-east"):

            def mutation(name: str, revision: int, selected_camera: str = camera) -> Mutation:
                return Mutation(request_id=f"{selected_camera}-{name}", expected_revision=revision)

            service.configure(camera, mutation("configure", 0))
            service.acquire(camera, f"{camera}-fit", mutation("capture", 1))
            service.fit(camera, f"{camera}-fit", f"{camera}-candidate", mutation("fit", 2))
            result = service.validate(
                camera, f"{camera}-candidate", f"{camera}-unused-final", mutation("validate", 3)
            )
            report = service.report(result.record_ids[0])
            if not report.passed:
                print(json.dumps(report.model_dump(mode="json"), indent=2))
                raise SystemExit(2)
            service.store.approve(
                camera,
                f"{camera}-candidate",
                report.report_id,
                args.actor,
                mutation("approve", result.state.revision),
            )
        service.prepare_tool("camera-west", Mutation(request_id="demo-tool", expected_revision=6))
        print(guided_pick(engine, "demo-pick"))
        return
    if args.operation == "pick":
        print(guided_pick(engine, args.request_id))
        return
    if args.expected_revision is None:
        parser.error("--expected-revision is required for mutations; inspect status first")
    request = Mutation(request_id=args.request_id, expected_revision=args.expected_revision)
    try:
        if args.operation == "configure":
            result = service.configure(args.camera, request)
        elif args.operation == "capture":
            result = service.acquire(
                args.camera,
                args.dataset,
                request,
                repeated_pose=args.repeated_poses,
                scenario=args.scenario,
            )
        elif args.operation == "fit":
            result = service.fit(args.camera, args.dataset, args.candidate, request)
        elif args.operation == "validate":
            result = service.validate(args.camera, args.candidate, args.dataset, request)
        elif args.operation == "reuse-estimate":
            result = service.reuse_estimate(args.camera, args.artifact, args.candidate, request)
        elif args.operation == "tool-check":
            result = service.prepare_tool(args.camera, request)
        elif args.operation == "routine-check":
            result = service.routine_check(args.camera, request)
        elif args.operation == "begin-measurements":
            result = service.begin_measurements(args.camera, request)
        elif args.operation == "move-camera":
            result = service.move_camera(args.camera, request, (0.04, 0.0, 0.0), (0.0, 0.025, 0.0))
        elif args.operation == "fault":
            result = service.introduce_fault(args.camera, args.kind, request)
        elif args.operation == "investigate":
            result = service.investigate(args.camera, args.kind, args.identity, request)
        else:
            result = service.store.approve(
                args.camera, args.candidate, args.report, args.actor, request
            )
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    except CalibrationError as error:
        print(json.dumps(error.as_dict(), indent=2))
        raise SystemExit(2) from None


def guided_pick(engine: Engine, request_id: str) -> str:
    """Same durable 22-stage approvals as the browser, including physical consent."""
    guided = GuidedEngine(engine)
    session = guided.create(
        CreateSession(
            request_id=request_id,
            request=OrderRequest(
                order_id=f"order-{request_id}",
                lines=(
                    OrderLine(
                        order_line_id=f"line-{request_id}",
                        product_id=engine.settings.products[0].product_id,
                        source_id="source",
                        destination_id="destination",
                    ),
                ),
            ),
        )
    )
    for _ in range(24):
        if session.status in ("COMPLETED", "FAILED", "UNKNOWN_OUTCOME"):
            break
        assert session.pending_authorization is not None
        session = guided.authorize(
            session.session_id,
            AuthorizeStage(
                request_id=f"{request_id}-{session.pending_authorization.stage}",
                expected_revision=session.revision,
                stage=session.pending_authorization.stage,
            ),
        )
    if session.status != "COMPLETED":
        print(json.dumps(session.model_dump(mode="json"), indent=2))
        raise SystemExit(2)
    return json.dumps(session.model_dump(mode="json"), indent=2)


if __name__ == "__main__":
    main()
