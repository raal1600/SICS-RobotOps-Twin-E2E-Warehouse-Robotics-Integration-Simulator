# Reproducible toolchain

Python is pinned in `.python-version`; `uv.lock` pins every resolved dependency
and wheel hash for runtime, tests and documentation. Use `uv sync --locked --all-groups`.
Do not update dependencies implicitly during tests. Updates require lock review,
the full suite and security checks. CI uses CPU execution and no model account.

Ruff checks new Python formatting/lint; mypy strict checks all runtime and API
modules. The pre-existing publication generator retains its separate build and
link/PDF checks. Coverage must be at least 85% for the combined mandatory suite;
the threshold is fixed before implementation and must not be lowered to pass.
Bandit plus pip-audit are the selected security checks; reviewed exceptions, if
needed, must identify the advisory, scope and rationale. No blanket exceptions.

Blender 5.2.1 LTS is the selected real-runtime acceptance executable. Mandatory
headless logic tests always run. The Blender acceptance lane must fail explicitly
when the executable is missing, never skip or silently fall back to a fake runtime.
