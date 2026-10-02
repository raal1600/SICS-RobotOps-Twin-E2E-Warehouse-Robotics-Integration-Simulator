.PHONY: setup test lint typecheck demo acceptance docs security
setup:
	uv sync --locked --all-groups
test lint typecheck demo acceptance docs security:
	uv run --locked python -m tools.dev $@
