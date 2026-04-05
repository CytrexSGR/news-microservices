.PHONY: dev prod build rebuild rebuild-dev logs logs-all health test clean help

# Default target
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

##@ Development Commands

dev: ## Start all services in development mode (hot-reload enabled)
	@echo "$(GREEN)Starting development environment...$(NC)"
	@echo "$(YELLOW)Features: Hot-reload, volume mounting, debug logging$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-build: ## Build and start development environment
	@echo "$(GREEN)Building and starting development environment...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-d: ## Start development environment in background
	@echo "$(GREEN)Starting development environment (detached)...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ Services started in background$(NC)"
	@echo "$(YELLOW)Run 'make logs' to view logs$(NC)"

##@ Production Commands

prod: ## Start all services in production mode
	@echo "$(GREEN)Starting production environment...$(NC)"
	@echo "$(YELLOW)Note: No hot-reload, optimized images$(NC)"
	docker-compose up

prod-d: ## Start production environment in background
	@echo "$(GREEN)Starting production environment (detached)...$(NC)"
	docker-compose up -d

##@ Build Commands

build: ## Build all services (production)
	@echo "$(GREEN)Building all services...$(NC)"
	docker-compose build

build-dev: ## Build all services (development)
	@echo "$(GREEN)Building all development services...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

rebuild: ## Force rebuild specific service (production)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make rebuild SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Rebuilding $(SERVICE)...$(NC)"
	docker-compose build --no-cache $(SERVICE)
	docker-compose up -d $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) rebuilt and restarted$(NC)"

rebuild-dev: ## Force rebuild specific service (development)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make rebuild-dev SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Rebuilding $(SERVICE) (development)...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache $(SERVICE)
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) rebuilt and restarted$(NC)"

##@ Monitoring Commands

logs: ## Show logs for specific service
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make logs SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	docker-compose logs -f $(SERVICE)

logs-all: ## Show logs for all services
	@echo "$(GREEN)Showing logs for all services...$(NC)"
	docker-compose logs -f

health: ## Check health status of all services
	@echo "$(BLUE)=== Service Health Status ===$(NC)"
	@for service in auth-service feed-service content-analysis-service research-service osint-service notification-service search-service analytics-service; do \
		port=$$(docker-compose port $$service 2>/dev/null | cut -d: -f2); \
		if [ -n "$$port" ]; then \
			status=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$$port/health 2>/dev/null); \
			if [ "$$status" = "200" ]; then \
				echo "$(GREEN)✓ $$service (port $$port): Healthy$(NC)"; \
			else \
				echo "$(RED)✗ $$service (port $$port): Unhealthy (HTTP $$status)$(NC)"; \
			fi; \
		else \
			echo "$(YELLOW)⚠ $$service: Not running$(NC)"; \
		fi; \
	done
	@echo ""
	@echo "$(BLUE)=== Infrastructure Services ===$(NC)"
	@for service in postgres redis rabbitmq traefik; do \
		if docker-compose ps $$service 2>/dev/null | grep -q "Up"; then \
			echo "$(GREEN)✓ $$service: Running$(NC)"; \
		else \
			echo "$(RED)✗ $$service: Not running$(NC)"; \
		fi; \
	done

##@ Database Commands

db-migrate: ## Run database migrations for specific service
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make db-migrate SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Running migrations for $(SERVICE)...$(NC)"
	./scripts/run-migrations.sh $(SERVICE)

db-validate: ## Validate database migrations
	@echo "$(GREEN)Validating database migrations...$(NC)"
	./scripts/validate-migrations.sh

db-preflight: ## Run database pre-flight checks
	@echo "$(GREEN)Running database pre-flight checks...$(NC)"
	./scripts/migration-preflight.sh

##@ Testing Commands

test: ## Run API workflow test
	@echo "$(GREEN)Running API workflow test...$(NC)"
	./scripts/test-api-workflow.sh

##@ Cleanup Commands

clean: ## Stop and remove all containers, networks, volumes
	@echo "$(RED)Stopping and removing all containers...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-dev: ## Stop and remove development containers
	@echo "$(RED)Stopping and removing development containers...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

##@ Utility Commands

ps: ## List all running containers
	@docker-compose ps

restart: ## Restart specific service
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make restart SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Restarting $(SERVICE)...$(NC)"
	docker-compose restart $(SERVICE)
	@echo "$(GREEN)✓ $(SERVICE) restarted$(NC)"

shell: ## Open shell in specific service container
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: SERVICE not specified$(NC)"; \
		echo "$(YELLOW)Usage: make shell SERVICE=content-analysis-service$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Opening shell in $(SERVICE)...$(NC)"
	docker-compose exec $(SERVICE) /bin/bash

help: ## Display this help message
	@echo ""
	@echo "$(BLUE)News Microservices - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-18s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make dev                              # Start development environment"
	@echo "  make logs SERVICE=feed-service        # View feed service logs"
	@echo "  make rebuild-dev SERVICE=auth-service # Rebuild auth service (dev)"
	@echo "  make health                           # Check all service health"
	@echo "  make db-migrate SERVICE=feed-service  # Run migrations"
	@echo ""
