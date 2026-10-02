"""Synchronize current status sources without editing generated publication output."""

import json
import re
import sys
from pathlib import Path


def update(phase: str, summary: str) -> None:
    status = {"phase": phase, "status": "NOT DONE", "summary": summary}
    Path("publication/status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    for path in Path("reports").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        replacement = (
            "<!-- implementation-status:start -->\n"
            "> **Implementation status, 2026-10-02:** " + summary + " Status: NOT DONE.\n"
            "> Evidence: GOAL_PROGRESS.md and ACCEPTANCE_REPORT.md in the governance section.\n"
            "> The research below records design rationale, not real-world robot validation.\n"
            "<!-- implementation-status:end -->"
        )
        text = re.sub(
            r"<!-- implementation-status:start -->.*?<!-- implementation-status:end -->",
            lambda _, replacement=replacement: replacement,
            text,
            flags=re.DOTALL,
        )
        path.write_text(text, encoding="utf-8")
    path = Path("README.md")
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r"\*\*Aktuell status:\*\*.*?(?=\n\n)",
        lambda _: (
            "**Aktuell status:** "
            + summary
            + " **NOT DONE** until all MUST criteria and remote workflows pass."
        ),
        text,
        flags=re.DOTALL,
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    update(sys.argv[1], sys.argv[2])
