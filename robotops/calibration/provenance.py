"""Allowlisted source snapshots for calculation provenance; no arbitrary file browser."""

import ast
import hashlib
import json
import sys
from collections.abc import Callable
from functools import lru_cache, partial
from pathlib import Path
from types import CodeType, FunctionType, MethodType

from robotops.calibration.errors import CalibrationError

ROOT = Path(__file__).resolve().parents[2]
MODULES = (
    "acquisition",
    "agreement",
    "artifacts",
    "checks",
    "configuration",
    "contracts",
    "depth",
    "diagnostics",
    "errors",
    "estimation",
    "faults",
    "geometry",
    "inspection",
    "investigation",
    "lifecycle",
    "measurement_quality",
    "optics",
    "outcome",
    "perception",
    "presentation",
    "provenance",
    "registration",
    "replay",
    "reproduction",
    "runtime_contracts",
    "service",
    "synthetic",
    "tcp",
    "trace",
    "validation",
    "visualization",
)
SOURCE_PATHS = (
    *tuple(f"robotops/calibration/{module}.py" for module in MODULES),
    "robotops/cell/calibration_sensor.py",
    "robotops/cell/calibration_execution.py",
    "robotops/cell/calibration_motion.py",
    "robotops/cell/runtime.py",
    "robotops/observation/calibrated.py",
    "robotops/brain/calibrated.py",
)


def source_fingerprints() -> dict[str, str]:
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in SOURCE_PATHS}


def source_snapshot(path: str, symbol: str) -> dict[str, object]:
    if path not in SOURCE_PATHS:
        raise CalibrationError("SOURCE_NOT_ALLOWLISTED")
    resolved = (ROOT / path).resolve()
    if not resolved.is_relative_to(ROOT):
        raise CalibrationError("SOURCE_NOT_ALLOWLISTED")
    raw = resolved.read_bytes()
    content = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    nodes = ast.parse(content).body
    selected = None
    for name in symbol.split("."):
        selected = next(
            (
                node
                for node in nodes
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == name
            ),
            None,
        )
        if selected is None:
            raise CalibrationError("SOURCE_SYMBOL_NOT_FOUND")
        nodes = selected.body
    if selected is None:
        raise CalibrationError("SOURCE_SYMBOL_NOT_FOUND")
    start = (
        min(selected.lineno, *(d.lineno for d in selected.decorator_list))
        if selected.decorator_list
        else selected.lineno
    )
    end = selected.end_lineno or selected.lineno
    return {
        "path": path,
        "symbol": symbol,
        "content": content,
        "displayed_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "file_bytes_sha256": hashlib.sha256(raw).hexdigest(),
        "symbol_start_line": start,
        "symbol_end_line": end,
        "excerpt": "\n".join(content.splitlines()[start - 1 : end]),
    }


def _constant(value: object) -> object:
    if isinstance(value, CodeType):
        return _code_record(value)
    if isinstance(value, tuple | frozenset):
        values = [_constant(item) for item in value]
        return {
            type(value).__name__: sorted(values, key=repr)
            if isinstance(value, frozenset)
            else values
        }
    if value is None or value is Ellipsis or type(value) in (bool, int, float, complex, str, bytes):
        return {"type": type(value).__name__, "value": repr(value)}
    raise CalibrationError("UNSUPPORTED_LOADED_CODE_CONSTANT", type(value).__name__)


def _code_record(code: CodeType) -> dict[str, object]:
    return {
        "qualname": code.co_qualname,
        "bytecode": code.co_code.hex(),
        "constants": [_constant(value) for value in code.co_consts],
        "names": code.co_names,
        "varnames": code.co_varnames,
        "freevars": code.co_freevars,
        "cellvars": code.co_cellvars,
        "flags": code.co_flags,
        "argcount": code.co_argcount,
        "posonlyargcount": code.co_posonlyargcount,
        "kwonlyargcount": code.co_kwonlyargcount,
        "stacksize": code.co_stacksize,
        "first_line": code.co_firstlineno,
        "line_table": code.co_linetable.hex(),
        "exception_table": code.co_exceptiontable.hex(),
    }


def _code_hash(code: CodeType) -> str:
    return hashlib.sha256(json.dumps(_code_record(code), sort_keys=True).encode()).hexdigest()


@lru_cache(maxsize=32)
def _compiled_functions(content: str, filename: str, optimize: int) -> dict[str, str]:
    # Compile only reviewed, allowlisted local text. Never execute compiled or archived
    # source; imports, decorators and module statements are not run by this comparison.
    root = compile(content, filename, "exec", dont_inherit=True, optimize=optimize)
    found = {}
    pending = [root]
    while pending:
        code = pending.pop()
        found[code.co_qualname] = _code_hash(code)
        pending.extend(value for value in code.co_consts if isinstance(value, CodeType))
    return found


def verify_loaded_callable(
    snapshot: dict[str, object], path: str, symbol: str, call: Callable[..., object]
) -> dict[str, object]:
    """Bind this direct/partial Python call to saved code, not its entire dependency closure."""
    function: object = call
    while isinstance(function, partial):
        function = function.func
    if isinstance(function, MethodType):
        function = function.__func__
    if not isinstance(function, FunctionType):
        raise CalibrationError("DIRECT_PYTHON_CALL_REQUIRED")
    if (
        path not in SOURCE_PATHS
        or function.__module__.replace(".", "/") + ".py" != path
        or function.__qualname__ != symbol
        or Path(function.__code__.co_filename).resolve() != (ROOT / path).resolve()
    ):
        raise CalibrationError("LOADED_CALLABLE_IDENTITY_MISMATCH")
    content = snapshot.get("content")
    if not isinstance(content, str):
        raise CalibrationError("SOURCE_SNAPSHOT_CONTENT_REQUIRED")
    compiled = _compiled_functions(content, str((ROOT / path).resolve()), sys.flags.optimize)
    actual_hash = _code_hash(function.__code__)
    if actual_hash != compiled.get(symbol):
        raise CalibrationError(
            "LOADED_SOURCE_MISMATCH",
            "The saved function differs from loaded Python code. Restart with a consistent source before calculating.",
        )
    return {
        "loaded_function_verification": "MATCHED_PYTHON_CODE",
        "code_fingerprint_method": "python-code-structure-v1",
        "loaded_code_sha256": actual_hash,
        "compiled_source_code_sha256": compiled[symbol],
        "python_version": sys.version,
        "optimization_level": sys.flags.optimize,
        "scope": "Saved source matched the loaded Python function and nested code at this call. Global objects, native libraries and the full dependency closure are not attested; software/source manifests remain separate.",
    }
