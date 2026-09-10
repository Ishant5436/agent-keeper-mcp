.PHONY: all test demo lint clean

all: test

test:
	uv run --with pytest --with hypothesis python -m pytest -v

demo:
	python3 demo.py

lint:
	uv run ruff check src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
