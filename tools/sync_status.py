"""Synchronize current status sources without editing generated publication output."""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

from tools.drift_check import criterion_ids


def completion_status(manifest: dict | None) -> str:
    if manifest is None:
        return "NOT DONE"
    if not all(
        manifest.get("criteria", {}).get(ident, {}).get("passed", False)
        for ident in criterion_ids()
    ):
        raise ValueError("Every MUST needs PASS evidence before completion")
    if not all(
        manifest.get("gates", {}).get(gate, {}).get("passed", False)
        for gate in ("ci", "publication_remote", "pages")
    ):
        raise ValueError("Remote CI and Pages evidence required before completion")
    return "DONE"


def update(phase: str, summary: str, completion_manifest: Path | None = None) -> None:
    manifest = json.loads(completion_manifest.read_text()) if completion_manifest else None
    state = completion_status(manifest)
    status_date = datetime.now(UTC).date().isoformat()
    status = {"phase": phase, "status": state, "summary": summary}
    Path("publication/status.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    for path in Path("reports").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        replacement = (
            "<!-- implementation-status:start -->\n"
            f"> **Implementation status, {status_date}:** " + summary + f" Status: {state}.\n"
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
        lambda _: "**Aktuell status:** " + summary + f" **{state}**.",
        text,
        flags=re.DOTALL,
    )
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    update(sys.argv[1], sys.argv[2], Path(sys.argv[3]) if len(sys.argv) > 3 else None)
