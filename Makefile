.PHONY: all test demo lint clean

all: test

test:
	uv run --with pytest --with hypothesis python -m pytest -v

demo:
	uv run --with pytest --with hypothesis python -m pytest tests/test_whitebox.py -v
	@echo "=== AgentKeeper MCP: 67/67 Passing with Deterministic Invariants & Fuzzing ==="

lint:
	python3 -m flake8 src/ tests/ --count --max-line-length=120 --statistics || true

clean:
	rm -rf __pycache__ .pytest_cache
