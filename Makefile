.PHONY: help install dev build test clean docker-up docker-down logs db-reset setup setup-frontend \
  dev-frontend dev-backend dev-ai dev-etl prod env-dev env-prod \
  shell-backend shell-frontend shell-ai shell-etl shell-db shell-pgadmin shell-weaviate \
  up down restart build-all prune ps \
  k8s-apply-dev k8s-apply-prod k8s-delete-dev k8s-delete-prod k8s-status k8s-logs k8s-shell \
  etl-run etl-clean

# Default target
help:
	@echo "Bookstore Management Commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev              - Start all services in development mode"
	@echo "  dev-frontend     - Start frontend development server"
	@echo "  dev-backend      - Start backend development server"
	@echo "  dev-ai           - Start AI service development server"
	@echo "  dev-etl          - Run ETL service for data loading"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up        - Start all services with Docker Compose"
	@echo "  docker-down      - Stop all Docker services"
	@echo "  build-all        - Build all Docker images"
	@echo "  etl-run          - Run ETL service to load data"
	@echo "  etl-clean        - Clean ETL data and restart"
	@echo ""
	@echo "Database:"
	@echo "  db-reset         - Reset database and reload data"
	@echo "  shell-db         - Access PostgreSQL shell"
	@echo ""
	@echo "Production:"
	@echo "  prod             - Start production environment"
	@echo "  k8s-apply-dev    - Deploy to development Kubernetes"
	@echo "  k8s-apply-prod   - Deploy to production Kubernetes"

# Installation and Setup
install:
	@echo "Installing dependencies..."
	cd client && npm install
	cd services/backend-service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd services/ai-service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd services/etl-service && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

setup: install
	@echo "Setting up development environment..."
	@echo "Please run the following commands manually:"
	@echo "1. Start PostgreSQL: sudo systemctl start postgresql"
	@echo "2. Start Redis: sudo systemctl start redis"
	@echo "3. Set up environment variables in .env file"
	@echo "4. Run 'make dev' to start development servers"

# Development Commands
dev: dev-backend dev-ai dev-frontend

dev-frontend:
	@echo "Starting frontend development server..."
	cd client && npm run dev

dev-backend:
	@echo "Starting backend development server..."
	cd services/backend-service && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-ai:
	@echo "Starting AI service development server..."
	cd services/ai-service && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

dev-etl:
	@echo "Running ETL service..."
	cd services/etl-service && source venv/bin/activate && python app/main.py

# Docker Commands
docker-up:
	@echo "Starting all services with Docker Compose..."
	docker-compose up -d

docker-down:
	@echo "Stopping all Docker services..."
	docker-compose down

build-all:
	@echo "Building all Docker images..."
	docker-compose build --no-cache

etl-run:
	@echo "Running ETL service to load data..."
	docker-compose --profile etl up etl-service

etl-clean:
	@echo "Cleaning ETL data and restarting..."
	docker-compose down
	docker volume rm bookstore_postgres_data
	docker-compose up -d postgres
	sleep 10
	make etl-run

# Database Commands
db-reset:
	@echo "Resetting database..."
	docker-compose down
	docker volume rm bookstore_postgres_data
	docker-compose up -d postgres
	sleep 10
	make etl-run

shell-db:
	@echo "Accessing PostgreSQL shell..."
	docker exec -it bookstore_postgres psql -U bookstore_user -d bookstore_db

# Shell Access
shell-backend:
	docker exec -it bookstore_backend_service /bin/bash

shell-frontend:
	docker exec -it bookstore_frontend /bin/bash

shell-ai:
	docker exec -it bookstore_ai_service /bin/bash

shell-etl:
	docker exec -it bookstore_etl_service /bin/bash

shell-pgadmin:
	docker exec -it bookstore_pgadmin /bin/bash

shell-weaviate:
	docker exec -it bookstore_weaviate /bin/bash

# Utility Commands
logs:
	docker-compose logs -f

prune:
	docker system prune -f

ps:
	docker-compose ps

# Production Commands
prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.yml up -d

# Kubernetes Commands
k8s-apply-dev:
	kubectl apply -k k8s/overlays/dev

k8s-apply-prod:
	kubectl apply -k k8s/overlays/prod

k8s-delete-dev:
	kubectl delete -k k8s/overlays/dev

k8s-delete-prod:
	kubectl delete -k k8s/overlays/prod

k8s-status:
	kubectl get pods -n bookstore

k8s-logs:
	kubectl logs -f deployment/bookstore-backend -n bookstore

k8s-shell:
	kubectl exec -it deployment/bookstore-backend -n bookstore -- /bin/bash

# Cleanup
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f
	rm -rf client/node_modules
	rm -rf services/*/venv
	rm -rf services/*/__pycache__
	rm -rf services/*/app/__pycache__