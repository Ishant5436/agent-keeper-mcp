.PHONY: all test demo lint clean

all: test

test:
	uv run --with pytest --with hypothesis python -m pytest -v

demo:
	python3 demo.py

lint:
	uv run --with flake8 python -m flake8 src/ tests/ --count --max-line-length=120 --statistics

clean:
	rm -rf __pycache__ .pytest_cache
