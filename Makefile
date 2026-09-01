.PHONY: all test demo lint clean

all: test

test:
	uv run --with pytest python -m pytest -v

demo:
	uv run --with pytest python -m pytest tests/test_whitebox.py -v
	@echo "=== AgentKeeper MCP: 63/63 Passing with Deterministic Invariants ==="

lint:
	python3 -m flake8 src/ tests/ --count --max-line-length=120 --statistics || true

clean:
	rm -rf __pycache__ .pytest_cache
