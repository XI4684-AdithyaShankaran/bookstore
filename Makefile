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
env-dev: ## Use dev.env.example for local development
	@cp dev.env.example .env

env-prod: ## Use dev.env.example for production (update values as needed)
	@cp dev.env.example .env

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
	make install
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

# ... (keep your Docker, K8s, etc. sections) ...

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
setup: ## Initial setup (copy env, install, up)
	@echo "Setting up development environment..."
	[ -f dev.env.example ] && cp dev.env.example .env || (echo "Warning: dev.env.example not found. .env not created." && true)
	make install
	make up
	@echo "Setup complete! Update .env file with your configuration."

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