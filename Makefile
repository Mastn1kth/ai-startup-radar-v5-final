# AI Startup Radar - Makefile

.PHONY: help build up down logs shell backend frontend test lint format

help: ## Show this help
	@echo "AI Startup Radar - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## Show logs
	docker-compose logs -f

shell-backend: ## Open backend shell
	docker-compose exec backend bash

shell-frontend: ## Open frontend shell
	docker-compose exec frontend sh

shell-db: ## Open database shell
	docker-compose exec postgres psql -U radar -d ai_startup_radar

backend-logs: ## Show backend logs
	docker-compose logs -f backend

frontend-logs: ## Show frontend logs
	docker-compose logs -f frontend

celery-logs: ## Show celery logs
	docker-compose logs -f celery-worker celery-beat

migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

makemigrations: ## Create new migration
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

test: ## Run tests
	docker-compose exec backend pytest

lint: ## Run linters
	docker-compose exec backend flake8 app/
	docker-compose exec backend black --check app/

format: ## Format code
	docker-compose exec backend black app/
	docker-compose exec backend isort app/

install-model: ## Install Ollama model
	docker-compose exec ollama ollama pull qwen2.5:14b

scrape: ## Run manual scraping
	docker-compose exec backend python -c "from app.tasks.scraping import scrape_source; scrape_source.delay('Product Hunt')"

analyze: ## Run AI analysis
	docker-compose exec backend python -c "from app.tasks.scraping import analyze_unprocessed_projects; analyze_unprocessed_projects.delay()"

score: ## Run scoring
	docker-compose exec backend python -c "from app.tasks.scraping import score_unscored_projects; score_unscored_projects.delay()"

report: ## Generate daily report
	docker-compose exec backend python -c "from app.tasks.reports import generate_daily_report; generate_daily_report.delay()"

clean: ## Clean up Docker
	docker-compose down -v
	docker system prune -f

restart: down up ## Restart all services

status: ## Show service status
	docker-compose ps