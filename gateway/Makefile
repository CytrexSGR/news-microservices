# Makefile for Traefik Gateway Management

.PHONY: help up down restart logs health test routes clean deploy rollback canary status config validate

# Variables
COMPOSE_FILE := docker-compose.yml
NAMESPACE := news-microservices
SERVICE_NAME := traefik

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

## Help
help:
	@echo "$(GREEN)Traefik Gateway Management Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Docker Commands:$(NC)"
	@echo "  make up              - Start Traefik gateway"
	@echo "  make down            - Stop Traefik gateway"
	@echo "  make restart         - Restart Traefik gateway"
	@echo "  make logs            - Show Traefik logs"
	@echo "  make status          - Show container status"
	@echo ""
	@echo "$(YELLOW)Configuration:$(NC)"
	@echo "  make config          - Validate configuration"
	@echo "  make reload          - Reload dynamic configuration"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  make health          - Run health checks"
	@echo "  make test            - Run all tests"
	@echo "  make routes          - Test all routes"
	@echo "  make perf            - Run performance tests"
	@echo ""
	@echo "$(YELLOW)Deployment:$(NC)"
	@echo "  make deploy          - Deploy to Kubernetes"
	@echo "  make canary SERVICE=<name> VERSION=<v2> - Start canary deployment"
	@echo "  make rollback        - Rollback deployment"
	@echo ""
	@echo "$(YELLOW)Certificates:$(NC)"
	@echo "  make certs           - Generate development certificates"
	@echo "  make certs-prod      - Request production certificates"
	@echo ""
	@echo "$(YELLOW)Maintenance:$(NC)"
	@echo "  make clean           - Clean up resources"
	@echo "  make backup          - Backup configuration"
	@echo "  make restore         - Restore configuration"

## Docker Commands
up: config
	@echo "$(GREEN)Starting Traefik Gateway...$(NC)"
	@docker compose -f $(COMPOSE_FILE) up -d
	@sleep 5
	@make health

down:
	@echo "$(YELLOW)Stopping Traefik Gateway...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down

restart: down up

logs:
	@docker compose -f $(COMPOSE_FILE) logs -f traefik

status:
	@echo "$(GREEN)Container Status:$(NC)"
	@docker compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "$(GREEN)Network Status:$(NC)"
	@docker network ls | grep news-microservices || echo "Network not found"

## Configuration Management
config: validate
	@echo "$(GREEN)Configuration is valid$(NC)"

validate:
	@echo "$(YELLOW)Validating Traefik configuration...$(NC)"
	@docker run --rm -v $(PWD)/traefik.yml:/etc/traefik/traefik.yml:ro \
		-v $(PWD)/config:/etc/traefik/config:ro \
		traefik:v2.10 validate /etc/traefik/traefik.yml || \
		(echo "$(RED)Configuration validation failed$(NC)" && exit 1)

reload:
	@echo "$(YELLOW)Reloading dynamic configuration...$(NC)"
	@docker exec -it news-gateway kill -USR1 1
	@echo "$(GREEN)Configuration reloaded$(NC)"

## Testing
health:
	@echo "$(GREEN)Running health checks...$(NC)"
	@./scripts/health-check.sh

test: health routes
	@echo "$(GREEN)All tests completed$(NC)"

routes:
	@echo "$(GREEN)Testing routes...$(NC)"
	@./scripts/test-routes.sh

perf:
	@echo "$(GREEN)Running performance tests...$(NC)"
	@if command -v ab &> /dev/null; then \
		ab -n 1000 -c 50 http://localhost/health; \
	else \
		echo "$(YELLOW)Apache Bench not installed, using curl$(NC)"; \
		time for i in $$(seq 1 100); do curl -s http://localhost/health > /dev/null; done; \
	fi

## Deployment
deploy:
	@echo "$(GREEN)Deploying to Kubernetes...$(NC)"
	@kubectl create namespace $(NAMESPACE) 2>/dev/null || true
	@kubectl apply -f k8s/rbac.yml
	@kubectl apply -f k8s/secrets.yml
	@kubectl apply -f k8s/configmap.yml
	@kubectl apply -f k8s/deployment.yml
	@echo "$(GREEN)Deployment complete$(NC)"
	@kubectl get pods -n $(NAMESPACE)

canary:
ifndef SERVICE
	@echo "$(RED)ERROR: SERVICE variable is required$(NC)"
	@echo "Usage: make canary SERVICE=auth-service VERSION=v2"
	@exit 1
endif
ifndef VERSION
	@echo "$(RED)ERROR: VERSION variable is required$(NC)"
	@echo "Usage: make canary SERVICE=auth-service VERSION=v2"
	@exit 1
endif
	@echo "$(GREEN)Starting canary deployment for $(SERVICE) version $(VERSION)...$(NC)"
	@./scripts/canary-rollout.sh $(SERVICE) $(VERSION)

rollback:
	@echo "$(YELLOW)Rolling back deployment...$(NC)"
	@./scripts/canary-rollout.sh --rollback
	@echo "$(GREEN)Rollback complete$(NC)"

## Certificate Management
certs:
	@echo "$(GREEN)Generating development certificates...$(NC)"
	@mkdir -p certs
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout certs/key.pem -out certs/cert.pem \
		-subj "/C=US/ST=State/L=City/O=NewsMCP/CN=*.news-mcp.local"
	@echo "$(GREEN)Development certificates generated$(NC)"

certs-prod:
	@echo "$(GREEN)Requesting production certificates...$(NC)"
	@docker exec news-gateway traefik certs request \
		--domains "api.news-mcp.local,*.api.news-mcp.local"

## Monitoring
metrics:
	@echo "$(GREEN)Fetching metrics...$(NC)"
	@curl -s http://localhost:8082/metrics | head -20

dashboard:
	@echo "$(GREEN)Opening Traefik Dashboard...$(NC)"
	@echo "URL: http://localhost:8080"
	@echo "Username: admin"
	@echo "Password: SecurePass123!"

## Maintenance
clean:
	@echo "$(YELLOW)Cleaning up resources...$(NC)"
	@docker compose -f $(COMPOSE_FILE) down -v
	@rm -rf logs/*.log
	@rm -f certs/*.pem
	@echo "$(GREEN)Cleanup complete$(NC)"

backup:
	@echo "$(GREEN)Backing up configuration...$(NC)"
	@mkdir -p backups
	@tar -czf backups/traefik-config-$$(date +%Y%m%d-%H%M%S).tar.gz \
		traefik.yml config/ k8s/ scripts/ .env
	@echo "$(GREEN)Backup created in backups/$(NC)"

restore:
ifndef BACKUP_FILE
	@echo "$(RED)ERROR: BACKUP_FILE variable is required$(NC)"
	@echo "Usage: make restore BACKUP_FILE=backups/traefik-config-20230101-120000.tar.gz"
	@exit 1
endif
	@echo "$(YELLOW)Restoring configuration from $(BACKUP_FILE)...$(NC)"
	@tar -xzf $(BACKUP_FILE)
	@echo "$(GREEN)Configuration restored$(NC)"

## Development
dev-up:
	@echo "$(GREEN)Starting development environment...$(NC)"
	@cp .env.example .env 2>/dev/null || true
	@docker compose -f $(COMPOSE_FILE) up

dev-logs:
	@docker compose -f $(COMPOSE_FILE) logs -f

## Troubleshooting
debug:
	@echo "$(YELLOW)Enabling debug mode...$(NC)"
	@docker exec news-gateway sh -c 'echo "log.level=DEBUG" >> /etc/traefik/traefik.yml'
	@make reload
	@echo "$(GREEN)Debug mode enabled$(NC)"

check-network:
	@echo "$(GREEN)Checking network connectivity...$(NC)"
	@docker exec news-gateway ping -c 2 auth-service || echo "Cannot reach auth-service"
	@docker exec news-gateway ping -c 2 feed-service || echo "Cannot reach feed-service"
	@docker exec news-gateway nslookup auth-service || echo "DNS resolution failed"

check-certs:
	@echo "$(GREEN)Checking SSL certificates...$(NC)"
	@openssl s_client -connect localhost:443 -servername api.news-mcp.local \
		-showcerts < /dev/null 2>/dev/null | \
		openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not After"

## Quick Commands
quick-test:
	@curl -s http://localhost/health | jq . || curl http://localhost/health

list-routes:
	@echo "$(GREEN)Configured Routes:$(NC)"
	@grep -E "rule:|service:" config/routes.yml | grep -v "#"

list-middlewares:
	@echo "$(GREEN)Configured Middlewares:$(NC)"
	@grep -E "^    [a-z-]+:" config/middlewares.yml | head -20

# Default target
.DEFAULT_GOAL := help