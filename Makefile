.PHONY: setup test lint typecheck demo acceptance docs security
setup:
	uv sync --locked --all-groups
	uv run --locked python -m playwright install chromium --only-shell
	cd tests/browser && npm ci --ignore-scripts --no-audit --no-fund
test lint typecheck demo acceptance docs security:
	uv run --locked python -m tools.dev $@
