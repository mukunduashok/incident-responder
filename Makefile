.PHONY: help install run format lint check test clean

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make run        - Run the FastAPI application"
	@echo "  make format     - Format code using ruff"
	@echo "  make lint       - Lint code using ruff"
	@echo "  make check      - Run format and lint checks"
	@echo "  make test       - Run tests with pytest"
	@echo "  make clean      - Remove cache and temporary files"

install:
	uv sync --all-extras

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

format:
	ruff format .
	ruff check --fix .

lint:
	ruff check .

check: lint
	ruff format --check .

test:
	pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +