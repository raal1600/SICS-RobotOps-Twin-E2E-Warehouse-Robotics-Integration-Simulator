"""Read-only access to the known Python files referenced by saved stages."""

import ast
import hashlib
from pathlib import Path
from typing import Any

from robotops.integration.engine import STAGES
from robotops.integration.inspection import COMPONENTS
from robotops.integration.models import SourceReference
from robotops.integration.store import sanitize

SOURCE_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = frozenset(stage[4] for stage in STAGES) | {item[1] for item in COMPONENTS.values()}


def symbol_range(content: str, symbol: str) -> tuple[int, int, str] | None:
    """Locate the complete named function/class, including its decorators, without execution."""
    try:
        nodes = ast.parse(content).body
        found = None
        for name in symbol.split("."):
            found = next(
                (
                    node
                    for node in nodes
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == name
                ),
                None,
            )
            if found is None:
                return None
            nodes = found.body
        if found is None:
            return None
        start = min([found.lineno, *(item.lineno for item in found.decorator_list)])
        return (
            start,
            found.end_lineno or found.lineno,
            "class" if isinstance(found, ast.ClassDef) else "function",
        )
    except SyntaxError:
        return None  # Redaction can intentionally make a source file non-executable.


def symbol_line(content: str, symbol: str) -> int | None:
    location = symbol_range(content, symbol)
    return location[0] if location else None


def current_source(reference: SourceReference) -> dict[str, Any]:
    """A current file is reference material, not an execution-time source snapshot."""
    result: dict[str, Any] = {
        "path": reference.path,
        "symbol": reference.symbol,
        "status": "unavailable",
        "scope": "Current application file, not a snapshot of the code used by this saved run. Sensitive values are redacted.",
    }
    if reference.path not in SOURCE_PATHS:
        return {**result, "reason": "This source file is not available for inspection."}
    path = (SOURCE_ROOT / reference.path).resolve()
    if not path.is_relative_to(SOURCE_ROOT.resolve()):
        return {**result, "reason": "This source file is not available for inspection."}
    try:
        original = path.read_text(encoding="utf-8")
        content = str(sanitize(original))
    except (OSError, UnicodeError):
        return {**result, "reason": "This application does not have the Python file available."}
    excerpt = str(sanitize(reference.excerpt))
    position = content.find(excerpt) if excerpt.strip() else -1
    # Never highlight the wrong lines if redaction removed a multiline value.
    location = (
        symbol_range(original, reference.symbol)
        if len(original.splitlines()) == len(content.splitlines())
        else None
    )
    return {
        **result,
        "status": "available",
        "language": "python",
        "content": content,
        "line_count": len(content.splitlines()),
        "excerpt_start_line": content[:position].count("\n") + 1 if position >= 0 else None,
        "symbol_start_line": location[0] if location else None,
        "symbol_end_line": location[1] if location else None,
        "symbol_kind": location[2] if location else None,
        "displayed_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
