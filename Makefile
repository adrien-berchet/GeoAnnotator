# GeoAnnotator Makefile
# Simplified commands for local development

.PHONY: help start stop restart logs health test shell clean

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "GeoAnnotator - Available Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start all services
	@./start-local.sh

stop: ## Stop all services (keep data)
	@./stop-local.sh

clean: ## Stop all services and remove data
	@./stop-local.sh --clean

restart: ## Restart all services
	@docker-compose restart

logs: ## Show logs (all services)
	@docker-compose logs -f

logs-backend: ## Show backend logs only
	@docker-compose logs -f backend

logs-frontend: ## Show frontend logs only
	@docker-compose logs -f frontend

logs-db: ## Show database logs only
	@docker-compose logs -f db

health: ## Check health of all services
	@./check-health.sh

test: ## Run all tests
	@echo "Running backend tests..."
	@docker-compose exec backend pytest
	@echo "Running frontend tests..."
	@docker-compose exec frontend npm test

test-backend: ## Run backend tests only
	@docker-compose exec backend pytest

test-frontend: ## Run frontend tests only
	@docker-compose exec frontend npm test

test-coverage: ## Run tests with coverage
	@docker-compose exec backend pytest --cov --cov-report=html
	@echo "Coverage report: backend/htmlcov/index.html"

shell: ## Open Django shell
	@docker-compose exec backend python manage.py shell

shell-db: ## Open PostgreSQL shell
	@docker-compose exec db psql -U geoannotator geoannotator

migrate: ## Run database migrations
	@docker-compose exec backend python manage.py migrate

makemigrations: ## Create new migrations
	@docker-compose exec backend python manage.py makemigrations

superuser: ## Create a superuser
	@docker-compose exec backend python manage.py createsuperuser

backup: ## Backup database
	@mkdir -p backups
	@docker-compose exec -T db pg_dump -U geoannotator geoannotator | gzip > backups/backup-$$(date +%Y%m%d-%H%M%S).sql.gz
	@echo "Backup created in backups/"

restore: ## Restore database from backup (usage: make restore FILE=backups/backup.sql.gz)
	@gunzip -c $(FILE) | docker-compose exec -T db psql -U geoannotator geoannotator
	@echo "Database restored from $(FILE)"

cleanup-trash: ## Run trash cleanup command
	@docker-compose exec backend python manage.py cleanup_trash

ps: ## Show running containers
	@docker-compose ps

stats: ## Show container resource usage
	@docker stats --no-stream

build: ## Rebuild Docker images
	@docker-compose build

rebuild: ## Rebuild images without cache
	@docker-compose build --no-cache

exec-backend: ## Execute command in backend container (usage: make exec-backend CMD="python manage.py <command>")
	@docker-compose exec backend $(CMD)

exec-frontend: ## Execute command in frontend container (usage: make exec-frontend CMD="npm <command>")
	@docker-compose exec frontend $(CMD)

install-backend: ## Install backend dependencies
	@docker-compose exec backend pip install -r requirements/development.txt

install-frontend: ## Install frontend dependencies
	@docker-compose exec frontend npm install

lint-backend: ## Run backend linters
	@docker-compose exec backend black --check apps/
	@docker-compose exec backend flake8 apps/

lint-frontend: ## Run frontend linter
	@docker-compose exec frontend npm run lint

format-backend: ## Format backend code
	@docker-compose exec backend black apps/

format-frontend: ## Format frontend code
	@docker-compose exec frontend npm run format

dev: ## Start in development mode with logs
	@docker-compose up

prod: ## Start in production mode
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

down: ## Stop and remove containers
	@docker-compose down
