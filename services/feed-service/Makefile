.PHONY: help install run test clean docker-build docker-up docker-down migrate

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
SERVICE_NAME := feed-service
PORT := 8001

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 mypy pre-commit
	pre-commit install

run: ## Run the API server locally
	uvicorn app.main:app --reload --port $(PORT)

worker: ## Run Celery worker
	celery -A celery_worker worker --loglevel=info --concurrency=4

beat: ## Run Celery beat scheduler
	celery -A celery_worker beat --loglevel=info

flower: ## Run Celery Flower monitoring
	celery -A celery_worker flower

test: ## Run tests with coverage
	pytest --cov=app --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/test_feeds.py tests/test_tasks.py -v

test-integration: ## Run integration tests
	pytest tests/test_integration.py -v

lint: ## Run linting
	flake8 app/ tests/ --max-line-length=120
	mypy app/

format: ## Format code with black
	black app/ tests/ --line-length=120

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/

migrate-create: ## Create a new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

migrate-up: ## Apply migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

migrate-history: ## Show migration history
	alembic history --verbose

docker-build: ## Build Docker image
	docker build -t $(SERVICE_NAME):latest .

docker-up: ## Start services with Docker Compose
	$(DOCKER_COMPOSE) up -d

docker-down: ## Stop Docker Compose services
	$(DOCKER_COMPOSE) down

docker-logs: ## View Docker logs
	$(DOCKER_COMPOSE) logs -f

docker-ps: ## Show running containers
	$(DOCKER_COMPOSE) ps

docker-exec: ## Execute command in API container
	docker exec -it feed-service-api /bin/bash

docker-clean: ## Clean Docker resources
	$(DOCKER_COMPOSE) down -v
	docker system prune -f

db-shell: ## Connect to PostgreSQL shell
	docker exec -it news-postgres psql -U postgres -d news_feeds

redis-cli: ## Connect to Redis CLI
	docker exec -it news-redis redis-cli

rabbitmq-ui: ## Open RabbitMQ management UI
	@echo "Opening RabbitMQ Management UI..."
	@echo "URL: http://localhost:15672"
	@echo "Username: guest"
	@echo "Password: guest"

check-health: ## Check service health
	@curl -s http://localhost:$(PORT)/health | python -m json.tool

api-docs: ## Open API documentation
	@echo "Opening API documentation..."
	@echo "Swagger UI: http://localhost:$(PORT)/docs"
	@echo "ReDoc: http://localhost:$(PORT)/redoc"

dev: ## Run all services for development
	@echo "Starting development environment..."
	$(MAKE) docker-up
	@sleep 5
	$(MAKE) migrate-up
	$(MAKE) run