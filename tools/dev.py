"""Portable equivalents of top-level make commands (also on Windows)."""

import argparse
import subprocess
import sys


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "test",
            "lint",
            "typecheck",
            "demo",
            "acceptance",
            "docs",
            "security",
            "contracts",
        ],
    )
    args, rest = parser.parse_known_args()
    match args.command:
        case "test":
            run("-m", "pytest", *rest)
        case "lint":
            run("-m", "ruff", "check", ".")
            run("-m", "ruff", "format", "--check", ".")
        case "typecheck":
            run("-m", "mypy")
        case "docs":
            run("tools/build_publication.py")
        case "security":
            run("-m", "tools.security_check")
        case "contracts":
            run("-m", "tools.export_contracts")
        case "demo":
            run("-m", "robotops.demo", *rest)
        case "acceptance":
            run("-m", "tools.acceptance", *rest)


if __name__ == "__main__":
    main()
