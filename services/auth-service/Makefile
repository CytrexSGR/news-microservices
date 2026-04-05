.PHONY: help install test run docker-build docker-up docker-down clean migrate lint format

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests with coverage"
	@echo "  make run          - Run the service locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start services with docker-compose"
	@echo "  make docker-down  - Stop services"
	@echo "  make migrate      - Run database migrations"
	@echo "  make clean        - Clean temporary files"
	@echo "  make lint         - Run code linters"
	@echo "  make format       - Format code"

install:
	pip install -r requirements.txt

test:
	pytest --cov=app --cov-report=html --cov-report=term-missing

test-fast:
	pytest -x --ff

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f auth-service

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(name)"

migrate-down:
	alembic downgrade -1

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

lint:
	flake8 app/ tests/ --max-line-length=120
	mypy app/

format:
	black app/ tests/
	isort app/ tests/

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
