.PHONY: all test demo lint clean

all: test

test:
	uv run --with pytest --with hypothesis python -m pytest -v

demo:
	python3 demo.py

lint:
	/Users/ishantpanchal/.local/bin/ruff check src/ tests/

clean:
	rm -rf __pycache__ .pytest_cache
