.PHONY: all test demo lint audit-iso9001 clean

all: test

test:
	uv run --with pytest --with hypothesis python -m pytest -v

audit-iso9001:
	@echo "=== Verifying Agent Keeper MCP Against ISO/DIS 9001:2026 Standards ==="
	python3 scripts/audit_iso9001_compliance.py

demo:
	python3 demo.py

lint:
	uv run ruff check src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache target/
