import argparse
from pathlib import Path

import uvicorn

from apps.api.app import create_workspace_app
from robotops.blender.adapter import BlenderRuntime
from robotops.cell.runtime import SyntheticRuntime
from robotops.config import Settings
from robotops.http_server import UVICORN_LOOP


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
    app = create_workspace_app(
        args.data_dir,
        runtime_type=BlenderRuntime if args.runtime == "blender" else SyntheticRuntime,
        settings=settings,
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, loop=UVICORN_LOOP)


if __name__ == "__main__":
    main()
