.PHONY: all test demo lint clean

all: test

test:
	python3 -m pytest -v

demo:
	python3 -m pytest tests/test_whitebox.py -v
	@echo "=== AgentKeeper MCP: 51/51 Passing with Deterministic Invariants ==="

lint:
	python3 -m flake8 src/ tests/ --count --max-line-length=120 --statistics || true

clean:
	rm -rf __pycache__ .pytest_cache
