"""Repository knowledge-base checks; generated publication is checked by its builder."""

import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
CRITERION_PATTERN = r"(?:SC-[A-Z]+-\d{3}|HKM-VIS-MUST-\d{3}|UI-INV-MUST-\d{3}|LAB-MUST-\d{3})"


def criterion_ids(root: Path = ROOT, level: str = "MUST") -> set[str]:
    return set(
        re.findall(
            rf"\*\*({CRITERION_PATTERN}) {re.escape(level)}\*\*",
            (root / "SUCCESS_CRITERIA.md").read_text(encoding="utf-8"),
        )
    )


def archived_markdown(root: Path) -> tuple[dict[Path, dict], list[str]]:
    """Identify byte-verified relocated copies, never an entire evidence directory."""
    snapshots = {}
    errors = []
    for manifest in sorted(root.glob("docs/evidence/*/inputs.json")):
        name = manifest.relative_to(root).as_posix()
        try:
            manifest_bytes = manifest.read_bytes()
            data = json.loads(manifest_bytes)
            # Other historical inventory schemas do not declare these copies.
            if not isinstance(data, dict) or not ({"archive_root", "copied"} & data.keys()):
                continue
            archive = manifest.parent
            if (
                data.get("archive_root") != archive.relative_to(root).as_posix()
                or not archive.resolve().is_relative_to(root.resolve())
                or manifest.resolve().parent != archive.resolve()
                or not isinstance(data.get("copied"), list)
            ):
                raise ValueError("invalid archive root or copied inventory")
            verified = {}
            seen = set()
            for item in data["copied"]:
                if not isinstance(item, dict) or not isinstance(item.get("archive_path"), str):
                    raise ValueError("invalid copied entry")
                recorded = item["archive_path"]
                if Path(recorded).suffix != ".md":
                    continue
                relative = Path(recorded)
                destination = (root / relative).resolve()
                if (
                    relative.is_absolute()
                    or ".." in relative.parts
                    or relative.as_posix() != recorded
                    or not destination.is_relative_to(archive.resolve())
                    or item.get("archive_relative")
                    != destination.relative_to(archive.resolve()).as_posix()
                    or destination in seen
                ):
                    raise ValueError(f"invalid or duplicate Markdown destination: {recorded}")
                seen.add(destination)
                source = item.get("source")
                if (
                    not isinstance(source, str)
                    or not source
                    or Path(source).is_absolute()
                    or ".." in Path(source).parts
                    or Path(source).as_posix() != source
                    or source == recorded
                    or not isinstance(item.get("kind"), str)
                    or not item["kind"]
                    or not isinstance(item.get("sha256"), str)
                    or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
                    or type(item.get("bytes")) is not int
                    or item["bytes"] < 0
                ):
                    raise ValueError(f"invalid Markdown copy metadata: {recorded}")
                raw = destination.read_bytes()
                if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                    raise ValueError(f"Markdown snapshot bytes differ: {recorded}")
                verified[destination] = {
                    "path": recorded,
                    "source": source,
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "manifest": name,
                    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                }
            # Any invalid entry rejects this manifest's entire exemption set.
            snapshots.update(verified)
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid archived Markdown manifest: {name}: {exc}")
    return snapshots, errors


def check(root: Path = ROOT) -> dict:
    snapshots, errors = archived_markdown(root)
    checked = []
    paths = sorted(
        [
            *root.glob("*.md"),
            *root.glob("reports/**/*.md"),
            *root.glob("docs/**/*.md"),
            *root.glob("blender/**/*.md"),
        ]
    )
    parser = MarkdownIt()
    known_ids = criterion_ids(root) | criterion_ids(root, "SHOULD")
    refs = json.loads((root / "publication/references.json").read_text(encoding="utf-8"))
    source_ids = {item["id"] for item in refs}
    diagrams = json.loads((root / "publication/diagrams.json").read_text(encoding="utf-8"))
    for path in paths:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        snapshot = snapshots.get(path.resolve())
        if snapshot and (
            len(raw) != snapshot["bytes"] or hashlib.sha256(raw).hexdigest() != snapshot["sha256"]
        ):
            errors.append(f"Archived Markdown changed during check: {path.relative_to(root)}")
            snapshots.pop(path.resolve())
            snapshot = None
        checked.append(path.relative_to(root).as_posix())
        for ident in re.findall(rf"\b{CRITERION_PATTERN}\b", text):
            if ident not in known_ids:
                errors.append(f"Unknown criterion {ident}: {path.name}")
        for token in parser.parse(text):
            for child in token.children or []:
                if child.type not in {"link_open", "image"}:
                    continue
                link = child.attrGet("href") or child.attrGet("src") or ""
                url = urlsplit(link)
                if url.scheme or url.netloc or not url.path:
                    continue
                if snapshot:
                    # Verbatim evidence retains its original relative-link context.
                    continue
                target = (path.parent / unquote(url.path)).resolve()
                if not target.is_relative_to(root.resolve()) or not target.exists():
                    errors.append(
                        f"Broken repository link: {path.relative_to(root).as_posix()}: {link}"
                    )
        if path.parent.name == "reports":
            for ident in re.findall(r"\bS\d{2}\b", text):
                if ident not in source_ids:
                    errors.append(f"Unknown source {ident}: {path.name}")
            for ident in re.findall(r"\{\{figure:([^}]+)\}\}", text):
                if ident not in diagrams:
                    errors.append(f"Unknown diagram {ident}: {path.name}")
    mapping = json.loads((root / "docs/acceptance-map.json").read_text(encoding="utf-8"))
    if set(mapping) != known_ids:
        errors.append(f"Acceptance mapping mismatch: {sorted(set(mapping) ^ known_ids)}")
    for ident, item in mapping.items():
        for file in item["files"]:
            if not (root / file).is_file():
                errors.append(f"Missing criterion evidence source: {ident}: {file}")
    status = json.loads((root / "publication/status.json").read_text(encoding="utf-8"))
    for path in [root / "README.md", *root.glob("reports/*.md")]:
        if status["summary"] not in path.read_text(encoding="utf-8"):
            errors.append(f"Stale shared status: {path.name}")
    make_targets = {
        target
        for line in (root / "Makefile").read_text().splitlines()
        if line and not line.startswith(("\t", ".")) and ":" in line
        for target in line.split(":", 1)[0].split()
    }
    for command in ("setup", "test", "lint", "typecheck", "demo", "acceptance", "docs", "security"):
        if command not in make_targets:
            errors.append(f"Missing developer command: {command}")
    for source in (root / "tests").rglob("*.py"):
        if re.search(r"pytest\.(skip|xfail)|pytest\.mark\.(skip|skipif|xfail)", source.read_text()):
            errors.append(f"Mandatory test bypass: {source.relative_to(root)}")
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    secret_patterns = [
        r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
        r"gh[pousr]_[A-Za-z0-9]{30,}",
        r"AKIA[A-Z0-9]{16}",
    ]
    for name in tracked:
        path = root / name
        if not path.is_file() or path.suffix in {".png", ".pdf"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(re.search(pattern, text) for pattern in secret_patterns):
            errors.append(f"Possible credential in tracked file: {name}")
    return {
        "passed": not errors,
        "errors": errors,
        "files_checked": checked,
        "archived_markdown_snapshots": sorted(snapshots.values(), key=lambda item: item["path"]),
        "must_count": len(criterion_ids(root)),
        "source_count": len(source_ids),
        "diagram_count": len(diagrams),
        "credential_scan": "tracked text: private-key/token patterns",
    }


def main() -> None:
    result = check()
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts/drift.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
