# Reproducible toolchain

Python is pinned in `.python-version`; `uv.lock` pins every resolved dependency
and wheel hash for runtime, tests and documentation. Use `uv sync --locked --all-groups`.
Do not update dependencies implicitly during tests. Updates require lock review,
the full suite and security checks. CI uses CPU execution and no model account.
Node 20.17.0 runs the built-in JavaScript playback control tests; CI selects this
version explicitly. No npm dependency, browser CDN or Node process is required
by the application. The browser uses its built-in Canvas API.

Ruff checks new Python formatting/lint; mypy strict checks all runtime and API
modules. The pre-existing publication generator retains its separate build and
link/PDF checks. Coverage must be at least 85% for the combined mandatory suite;
the threshold is fixed before implementation and must not be lowered to pass.
Bandit plus pip-audit are the selected security checks; reviewed exceptions, if
needed, must identify the advisory, scope and rationale. No blanket exceptions.

`tools.security_check` saves full Bandit and pip-audit output. The five low-severity
subprocess findings are reviewed in [security-exceptions.json](../security-exceptions.json):
fixed Blender script/version and Python demo restart calls with no shell or model
code. Each exception is bound to a file, rule and AST hash of the enclosing
function/import. Any changed scope or higher severity fails. Dependency advisories
have no exceptions. WeasyPrint was upgraded to 70.0 to fix GHSA-jhhc-3hcp-qhm5 and
GHSA-jf6q-chmf-3h3v; the locked environment is audited again rather than suppressing
these findings. The advisory check uses the network during installation preflight,
separately from deterministic runtime tests.

Blender 5.2.1 LTS is the selected real-runtime acceptance executable. Mandatory
headless logic tests always run. The Blender acceptance lane must fail explicitly
when the executable is missing, never skip or silently fall back to a fake runtime.

The optional Windows desktop host builds with the Windows .NET Framework x64 C#
compiler and checksum-pinned Microsoft.Web.WebView2 1.0.3800.47. The installed
WebView2 Runtime receives Microsoft's normal security updates. Its separate
Windows CI lane compiles and tests the real window lifecycle. See [desktop build
and ownership details](desktop.md); no Python dependency or mandatory Blender
test is replaced by desktop packaging.
