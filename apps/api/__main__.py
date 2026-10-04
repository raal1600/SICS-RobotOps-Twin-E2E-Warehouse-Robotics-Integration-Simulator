import argparse
from pathlib import Path

import uvicorn

from apps.api.app import create_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.workflow.engine import Engine
from robotops.workflow.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="Local synthetic RobotOps Twin dashboard")
    parser.add_argument("--data-dir", type=Path, default=Path("runs/dashboard"))
    parser.add_argument("--runtime", choices=["headless", "blender"], default="headless")
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    settings = (
        Settings.model_validate_json(args.settings.read_text())
        if args.settings
        else Settings.hkm(visual_frame_seconds=1 / 24)
    )
    store = Store(args.data_dir / "workflow.db")
    runtime = (BlenderRuntime if args.runtime == "blender" else SyntheticRuntime)(
        args.data_dir / "runtime.db", settings
    )
    engine = Engine(store, runtime, runtime.settings)
    uvicorn.run(create_app(store, engine, recover=True), host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
