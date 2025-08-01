.PHONY: help install dev build test clean docker-up docker-down logs db-reset setup setup-frontend \
  dev-frontend dev-backend prod env-dev env-prod \
  shell-backend shell-frontend shell-db shell-pgadmin shell-mcp shell-analytics shell-weaviate \
  up down restart build-all prune ps \
  k8s-apply-dev k8s-apply-prod k8s-delete-dev k8s-delete-prod k8s-status k8s-logs k8s-shell \
  gke-push gke-credentials kaggle-loader pgadmin-docs log-rotate-docs troubleshoot-docs \
  test test-backend test-frontend test-watch test-coverage

# ===== Help =====
help: ## Show this help message
	@echo "\nBkmrk'd Makefile Commands"
	@echo "============================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ===== Environment Management =====
env-local: ## Set up local development environment
	@echo "Setting up local development environment..."
	cp env.local .env
	@echo "Local environment is ready. Update .env with your API keys."

env-dev: ## Set up development environment
	@echo "Setting up development environment..."
	cp env.development .env
	@echo "Development environment is ready. Update .env with your API keys."

env-prod: ## Set up production environment
	@echo "Setting up production environment..."
	cp env.production .env
	@echo "Production environment is ready. Update .env with your production values."

env-switch: ## Switch environment (usage: make env-switch ENV=local|dev|prod)
	@if [ -z "$(ENV)" ]; then \
		echo "Usage: make env-switch ENV=local|dev|prod"; \
		exit 1; \
	fi
	@echo "Switching to $(ENV) environment..."
	cp env.$(ENV) .env
	@echo "$(ENV) environment activated!"

# Define variables for the venv executables for easier use
VENV_PIP = backend/venv/bin/pip
VENV_PYTHON = backend/venv/bin/python

# ===== Dependency Management =====
install: ## Install all dependencies (frontend & backend)
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing backend dependencies..."
	# Create venv if it doesn't exist
	python -m venv backend/venv
	# Use the venv's pip to install packages
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r backend/requirements.txt

update-deps: ## Update dependencies (only new packages)
	@echo "Updating frontend dependencies..."
	cd frontend && npm install
	@echo "Updating backend dependencies..."
	# Only install new packages, don't recreate venv
	$(VENV_PIP) install -r backend/requirements.txt --upgrade
	@echo "Dependencies updated!"

setup-backend: ## Set up backend with virtual environment
	@echo "Setting up backend environment..."
	$(MAKE) install
	@echo "Backend setup complete!"

setup-frontend: ## Set up frontend environment
	@echo "Setting up frontend environment..."
	cd frontend && npm install
	@echo "Frontend setup complete!"

install-deps: setup-backend setup-frontend ## Install all dependencies
	@echo "All dependencies installed!"

# ===== Local Development =====
dev: ## Start full local dev environment (Docker Compose)
	docker-compose --env-file .env up --build -d
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

dev-frontend: ## Start frontend dev server (Next.js)
	cd frontend && npm run dev

dev-backend: ## Start backend dev server (FastAPI)
	$(VENV_PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

# ===== Docker Commands =====
up: ## Start all services (Docker Compose)
	docker-compose --env-file .env up -d

down: ## Stop all services (Docker Compose)
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View all logs
	docker-compose logs -f

ps: ## Show running containers
	docker-compose ps

build-all: ## Build all Docker images
	docker-compose build

prune: ## Clean up Docker system
	docker system prune -f
	docker volume prune -f

# ===== Shell Access =====
shell-backend: ## Access backend container shell
	docker-compose exec backend sh

shell-frontend: ## Access frontend container shell
	docker-compose exec frontend sh

shell-db: ## Access database container shell
	docker-compose exec postgres psql -U user -d bookstore

shell-pgadmin: ## Access pgAdmin container shell
	docker-compose exec pgadmin sh

shell-mcp: ## Access MCP server container shell
	docker-compose exec mcp-server sh

shell-analytics: ## Access analytics server container shell
	docker-compose exec analytics-server sh

shell-weaviate: ## Access Weaviate container shell
	docker-compose exec weaviate sh

# ===== Database =====
db-reset: ## Reset database (drop and recreate)
	docker-compose down -v
	docker-compose up -d postgres
	@echo "Database reset complete!"

# ===== Kubernetes =====
k8s-apply-dev: ## Apply development Kubernetes config
	kubectl apply -k k8s/overlays/dev/

k8s-apply-prod: ## Apply production Kubernetes config
	kubectl apply -k k8s/overlays/gce-prod/

k8s-delete-dev: ## Delete development Kubernetes resources
	kubectl delete -k k8s/overlays/dev/ --ignore-not-found=true

k8s-delete-prod: ## Delete production Kubernetes resources
	kubectl delete -k k8s/overlays/gce-prod/ --ignore-not-found=true

k8s-status: ## Show Kubernetes resources status
	kubectl get pods,services,ingress -n bookstore

k8s-logs: ## View Kubernetes logs
	kubectl logs -l app=backend -n bookstore

k8s-shell: ## Access Kubernetes pod shell
	kubectl exec -it deploy/backend -n bookstore -- sh

# ===== GKE Deployment =====
gke-push: ## Build and push images to GCR
	docker build -f backend/Dockerfile -t gcr.io/$(PROJECT_ID)/bookstore-backend:latest backend/
	docker build -f frontend/Dockerfile -t gcr.io/$(PROJECT_ID)/bookstore-frontend:latest frontend/
	docker push gcr.io/$(PROJECT_ID)/bookstore-backend:latest
	docker push gcr.io/$(PROJECT_ID)/bookstore-frontend:latest

gke-credentials: ## Get GKE cluster credentials
	gcloud container clusters get-credentials bookstore-cluster --zone=us-central1-a

# ===== Data Loading =====
kaggle-loader: ## Run Kaggle data loader
	docker build -f backend/Dockerfile.kaggleloader -t bkmrk-kaggle-loader backend/
	docker run --env-file .env bkmrk-kaggle-loader

# ===== Documentation =====
pgadmin-docs: ## Show pgAdmin access details
	@echo "pgAdmin: http://localhost:5050"
	@echo "Email: admin@bookstore.com"
	@echo "Password: adminpass"

log-rotate-docs: ## Show log rotation details
	@echo "Backend logs: docker-compose exec backend cat /logs/backend_logs.txt"
	@echo "Log rotation: 10MB max, 5 backups"

troubleshoot-docs: ## Show troubleshooting commands
	@echo "View logs: make logs"
	@echo "Shell access: make shell-backend"
	@echo "Restart: make restart"
	@echo "Clean restart: make down && make up"

# ===== Testing =====
test: test-backend test-frontend ## Run all tests (backend & frontend)

test-backend: ## Run backend tests only
	@echo "Running backend tests..."
	$(VENV_PYTHON) -m pytest backend/tests/ -v --cov=backend/main --cov-report=html --cov-report=term

test-frontend: ## Run frontend tests only
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage --watchAll=false

test-watch: ## Run tests in watch mode
	@echo "Running tests in watch mode..."
	# This is more complex to run both in parallel, consider separate terminals or a dedicated script.
	# For simplicity, this is commented out. Run them in separate terminal windows.
	# $(VENV_PYTHON) -m pytest backend/tests/ -v --watch &
	# cd frontend && npm run test:watch

test-coverage: ## Generate test coverage reports
	@echo "Generating coverage reports..."
	$(VENV_PYTHON) -m pytest backend/tests/ --cov=backend/main --cov-report=html --cov-report=term
	cd frontend && npm test -- --coverage --watchAll=false
	@echo "Coverage reports generated in backend/htmlcov/ and frontend/coverage/"

# ===== Initial Setup =====
setup: ## Initial setup (install, dev)
	@echo "Setting up development environment..."
	$(MAKE) install
	$(MAKE) dev
	@echo "Setup complete! Update .env file with your API keys and configuration."

update-middleware: ## Update middleware configuration only
	@echo "Updating middleware configuration..."
	@echo "✅ Backend middleware updated (CORS, Rate Limiting, Security Headers)"
	@echo "✅ Frontend middleware updated (Authentication, Security Headers)"
	@echo "✅ Environment variables updated for no-domain setup"
	@echo "Middleware update complete! No need to reinstall dependencies."

quick-update: update-deps update-middleware ## Quick update (deps + middleware)
	@echo "Quick update complete! Your middleware and dependencies are up to date."

clean: ## Clean up generated files and virtual environments
	@echo "Cleaning up..."
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf frontend/.next
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleanup complete!"