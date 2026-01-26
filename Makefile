.PHONY: help install run format lint check test test-unit test-integration test-e2e test-coverage test-watch clean secretscan qdrant

help:
	@echo "Available commands:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install all dependencies (production + dev + test)"
	@echo "  make run              - Run the FastAPI application"
	@echo "  make format           - Format code using ruff"
	@echo "  make lint             - Lint code using ruff"
	@echo "  make check            - Run format and lint checks"
	@echo "  make test             - Run all tests with coverage"
	@echo "  make test-unit        - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-e2e         - Run only end-to-end tests"
	@echo "  make test-coverage    - Run tests and generate coverage report"
	@echo "  make test-watch       - Run tests in watch mode"
	@echo "  make clean            - Remove cache and temporary files"
	@echo "  make secretscan       - Scan for secrets using trufflehog"

install:
	uv sync

install-dev:
	uv sync --all-groups

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
	pytest -v --cov=src/incident_responder --cov-report=term-missing --cov-report=html

test-unit:
	pytest tests/unit -v --cov=src/incident_responder --cov-report=term-missing

test-integration:
	pytest tests/integration -v --cov=src/incident_responder --cov-report=term-missing

test-e2e:
	pytest tests/e2e -v -m slow --timeout=300

test-coverage:
	pytest -v --cov=src/incident_responder --cov-report=term-missing --cov-report=html --cov-report=xml
	@echo "Coverage report generated in htmlcov/index.html"

test-watch:
	pytest-watch -- -v --cov=src/incident_responder --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete

secretscan:
	trufflehog git file://.

qdrant:
	docker run -p 6333:6333 qdrant/qdrant
