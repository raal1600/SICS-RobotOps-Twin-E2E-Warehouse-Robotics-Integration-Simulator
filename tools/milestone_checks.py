"""Capture actual gate output; a failed command fails the milestone."""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    name = sys.argv[1]
    results = []
    for command in ["test", "lint", "typecheck"]:
        args = [sys.executable, "-m", "tools.dev", command]
        result = subprocess.run(args, capture_output=True, text=True)
        results.append(
            {
                "command": "python -m tools.dev " + command,
                "exit_code": result.returncode,
                "output": result.stdout + result.stderr,
            }
        )
        print(result.stdout + result.stderr)
        if result.returncode:
            raise SystemExit(result.returncode)
    evidence = {
        "base": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "recorded_at": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "checks": results,
    }
    Path(f"docs/evidence/{name}-checks.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
