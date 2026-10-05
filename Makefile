.PHONY: setup test lint typecheck demo acceptance docs security
setup:
	uv sync --locked --all-groups
	uv run --locked python -m playwright install chromium --only-shell
test lint typecheck demo acceptance docs security:
	uv run --locked python -m tools.dev $@
