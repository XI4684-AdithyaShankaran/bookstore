# Bkmrk'd - Modern Bookstore Application

This is a NextJS + FastAPI full-stack application for a modern online bookstore.

## Tech Stack

- **Frontend**: Next.js 15 with TypeScript and Tailwind CSS
- **Backend**: FastAPI with Python
- **Database**: PostgreSQL
- **Caching**: Redis
- **Containerization**: Docker & Docker Compose
- **Deployment**: Kubernetes with Google Cloud Platform

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Git

### Local Development Setup (Without Docker)

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib redis-server netcat-openbsd lsof
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

**macOS:**
```bash
brew install python node postgresql redis netcat lsof
brew services start postgresql
brew services start redis
```

#### 2. Clone and Setup Environment
```bash
git clone <repository-url>
cd bookstore
cp env.development .env
```

#### 3. Setup Databases

**PostgreSQL:**
```bash
# Create database and user
sudo -u postgres psql -c "CREATE USER bookstore_user WITH PASSWORD 'bookstore_pass';"
sudo -u postgres psql -c "CREATE DATABASE bookstore_db OWNER bookstore_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bookstore_db TO bookstore_user;"
```

**Redis:**
```bash
# Start Redis with password
redis-server --port 6379 --daemonize yes --requirepass bookstore_redis_pass
```

#### 4. Setup Python Services

**Backend Service:**
```bash
cd services/backend-service
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..
```



**AI/ML Service (Consolidated - Recommendations, Analytics, Agentic Tools & Web Search):**
```bash
cd services/ai-ml-service
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..
```

**ETL Service (Data Loading):**
```bash
cd services/etl-service
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..
```

#### 5. Setup Frontend Client
```bash
cd client
npm install
cd ..
```

#### 6. Start All Services

**Start Backend Services (in separate terminals):**
```bash
# Terminal 1 - Backend Service (Main API)
cd services/backend-service
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - AI Service (ML + Recommendations + Analytics)
cd services/ai-service
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# Terminal 3 - ETL Service (Data Loading)
cd services/etl-service
source venv/bin/activate
python app/main.py
```

**Start Frontend Client:**
```bash
# Terminal 7 - Frontend Client
cd client
npm run dev
```

#### 7. Access the Application

- **Frontend**: http://localhost:3000
- **Backend Service**: http://localhost:8000
- **AI Service**: http://localhost:8003

#### 8. API Documentation

- **Backend API Docs**: http://localhost:8000/docs
- **AI Service Docs**: http://localhost:8003/docs

### Docker Development Setup (Alternative)

If you prefer using Docker:

```bash
docker-compose up -d
```

### Cleanup Commands

**Stop All Services:**
```bash
# Stop Python services
pkill -f "uvicorn"

# Stop Node.js services
pkill -f "npm run dev"
pkill -f "next dev"

# Stop databases
redis-cli -p 6379 -a bookstore_redis_pass shutdown
sudo systemctl stop postgresql
```

**Clean Up Files:**
```bash
# Remove log files
find . -name "*.log" -delete

# Remove Python cache
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +

# Remove Node.js cache
find . -name ".next" -type d -exec rm -rf {} +
```

**Full Cleanup (Remove Everything):**
```bash
# Stop all services first
pkill -f "uvicorn"
pkill -f "npm run dev"
pkill -f "next dev"
redis-cli -p 6379 -a bookstore_redis_pass shutdown

# Remove virtual environments
find . -name "venv" -type d -exec rm -rf {} +

# Remove node_modules
find . -name "node_modules" -type d -exec rm -rf {} +

# Remove cache files
find . -name "*.log" -delete
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name ".next" -type d -exec rm -rf {} +
```

### Individual Service Commands

**Start Individual Services:**
```bash
# Backend Service (Main API)
cd services/backend-service && source venv/bin/activate && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# AI/ML Service (Consolidated - Recommendations, Analytics, Agentic Tools & Web Search)
cd services/ai-ml-service && source venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload

# ETL Service (Data Loading)
cd services/etl-service && source venv/bin/activate && python app/main.py

# Frontend Client
cd client && npm run dev
```

**Database Commands:**
```bash
# Connect to PostgreSQL
psql -h localhost -U bookstore_user -d bookstore_db

# Connect to Redis
redis-cli -p 6379 -a bookstore_redis_pass

# Check if services are running
lsof -i :8000  # Check API Gateway
lsof -i :8001  # Check Backend Service
lsof -i :3000  # Check Frontend
lsof -i :5432  # Check PostgreSQL
lsof -i :6379  # Check Redis
```

### Environment Variables

The project includes a `.env` file with default development values. Update it with your specific configuration:

```env
# Required: Update these with your actual values
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-api-key

# Optional: Update for production
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Features

- **Infinite Scroll Book Grid**: Pinterest-style book browsing
- **Book Detail Views**: Detailed information about each book
- **User Authentication**: JWT-based authentication with OAuth support
- **AI Book Recommendations**: AI-powered book suggestions
- **Custom Bookshelves**: User-created book collections
- **Shopping Cart**: Add books to cart functionality

## Project Structure

```
bookstore/
├── frontend/              # Next.js 15 frontend application
├── services/              # Microservices architecture
│   ├── api-server/        # FastAPI main API server
│   ├── ai-ml-service/     # Consolidated AI/ML service (recommendations + analytics + agentic tools + web search)
│   ├── analytics-service/ # Analytics and metrics service
│   └── data-service/      # Data processing and ETL
├── k8s/                   # Kubernetes deployment configurations
├── docs/                  # Comprehensive project documentation
├── scripts/               # Automation and utility scripts
├── redis/                 # Redis configuration
└── docker-compose.yml     # Development environment orchestration
```

## Deployment

The application is configured for deployment on Google Cloud Platform using Kubernetes. See the `k8s/` directory for deployment configurations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

---

## 📚 Kaggle Data Loader: Local & Cloud Usage

### Local (Docker)
1. Set your Kaggle credentials and database URL in `.env` or export as environment variables:
   ```sh
   export KAGGLE_USERNAME=your_kaggle_username
   export KAGGLE_KEY=your_kaggle_key
   export DATABASE_URL=postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db
   ```
2. Build and run the loader:
   ```sh
   docker build -f services/backend-service/Dockerfile.kaggleloader -t bkmrk-kaggle-loader services/backend-service/
   docker run --env-file .env bkmrk-kaggle-loader
   ```

### Cloud (Kubernetes Job)
1. Build and push the loader image to your registry:
   ```sh
   docker build -f services/backend-service/Dockerfile.kaggleloader -t us-central1-docker.pkg.dev/bookstore-project-464717/bookstore/bkmrk-kaggle-loader:latest services/backend-service/
   docker push us-central1-docker.pkg.dev/bookstore-project-464717/bookstore/bkmrk-kaggle-loader:latest
   ```
2. Ensure your Kubernetes secrets contain `DATABASE_URL`, `KAGGLE_USERNAME`, and `KAGGLE_KEY`.
3. Apply the job manifest:
   ```sh
   kubectl apply -f k8s/base/kaggle-loader-job.yaml
   ```
4. Monitor the job:
   ```sh
   kubectl logs job/kaggle-loader -n bookstore
   ```

---

## 🌍 Dual Environment: Local & Cloud
- **Local:** Use Docker Compose for full-stack dev. All services (frontend, backend, Postgres, Redis, Weaviate, MCP, Analytics) run as containers. Access at `http://localhost:3000`.
- **Cloud:** Deploy to GKE. All config via K8s secrets/configmaps. Use GCP managed services for DB, cache, etc.
- **Dynamic Config:** All sensitive/configurable values (DB URLs, API keys, endpoints) are set via environment variables or secrets—never hardcoded.

---

## 🛠️ Dependency Management
- **Python:** Use `pip install -r requirements.txt` (or in Docker build). For local dev, use a venv: `python -m venv venv && source venv/bin/activate`.
- **Node.js:** Use `npm ci` for reproducible installs (never just `npm install` in CI/CD).

---

## 🦾 DuckDuckGo Search Agent
- The MCP server uses a DuckDuckGo agent to enrich book metadata (genres, descriptions) dynamically if missing.

---

## 🔒 Best Practices
- No hardcoded credentials or endpoints in code or configs.
- All configs are dynamic and production-grade.
- Both local and cloud setups are fully supported and documented.

---

## 🖥️ pgAdmin Setup and Usage

pgAdmin is a web-based interface for managing PostgreSQL databases. This section covers how to use pgAdmin both locally (via Docker Compose) and in the cloud (GKE).

### Local (Docker Compose)
- pgAdmin is included in `docker-compose.yml`.
- Access it at [http://localhost:5050](http://localhost:5050) after running `make up` or `docker-compose up`.
- **Login credentials:**
  - **Email:** `admin@bookstore.com`
  - **Password:** `adminpass`
- **Connect to PostgreSQL:**
  - **Host:** `postgres` (the service name in Docker Compose)
  - **Port:** `5432`
  - **Database:** as set in your `.env` (e.g., `bookstore`)
  - **Username/Password:** as set in your `.env`
- **Usage:**
  - View tables, run queries, manage the database, import/export data.

### Cloud (GKE)
- pgAdmin is deployed as a Kubernetes deployment and service.
- Access it via the Ingress external IP: `http://<external-ip>/pgadmin`
- **Login credentials:**
  - **Email:** `admin@bookstore.com`
  - **Password:** `adminpass`
- **Connect to PostgreSQL:**
  - **Host:** `postgres` (the K8s service name)
  - **Port:** `5432`
  - **Database:** as set in your K8s secret
  - **Username/Password:** as set in your K8s secret
- **Usage:**
  - Same as local: view tables, run queries, manage the database.

### Troubleshooting
- If you cannot log in, check your environment variables or K8s secrets for correct credentials.
- If you cannot connect to the database, ensure the `postgres` service is running and accessible from pgAdmin.
- For logs:
  - Local: `docker-compose logs pgadmin`
  - GKE: `kubectl logs -l app=pgadmin -n bookstore`

---

## 🌀 Log Rotation in FastAPI Backend

To prevent log files from growing indefinitely, the backend uses Python's `RotatingFileHandler` for log rotation.

- **Log file location:** `/logs/backend_logs.txt` (configurable via `LOG_DIR` env variable)
- **Rotation settings:**
  - Max size: 10 MB per file
  - Backups: 5 rotated files kept
- **How to view logs:**
  - Local: `cat logs/backend_logs.txt`
  - Docker Compose: `docker-compose exec backend cat /logs/backend_logs.txt`
  - GKE: `kubectl exec -it deploy/backend -n bookstore -- cat /logs/backend_logs.txt`
- **How it works:**
  - When the log file reaches 10 MB, it is rotated and a new file is started. Up to 5 old log files are kept as backups.

---

## 🛠️ Troubleshooting & Cleanup

### Common Issues & Fixes
- **Service won’t start (Docker/Compose):**
  - Run `make logs` or `docker-compose logs -f` to see error details.
  - Check for port conflicts or missing environment variables.
- **Database connection errors:**
  - Ensure Postgres is running and credentials match your `.env` or K8s secret.
  - For Compose: `make shell-db` and check logs.
  - For GKE: `kubectl logs -l app=postgres -n bookstore`
- **pgAdmin login fails:**
  - Double-check `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` in your env or secret.
- **Kubernetes pod stuck/crashloop:**
  - Run `kubectl get pods -n bookstore` and `kubectl describe pod <pod-name> -n bookstore`.
  - View logs: `kubectl logs <pod-name> -n bookstore`
- **Ingress not accessible (GKE):**
  - Wait for external IP to provision: `kubectl get ingress -n bookstore`
  - Check Ingress and service logs for errors.
- **SSL/TLS issues:**
  - See the SSL/TLS section below for certificate troubleshooting.

### Viewing Logs
- **Docker Compose:**
  - All logs: `make logs` or `docker-compose logs -f`
  - Specific service: `docker-compose logs backend`
- **Kubernetes/GKE:**
  - All backend logs: `kubectl logs -l app=backend -n bookstore`
  - All frontend logs: `kubectl logs -l app=frontend -n bookstore`
  - Pod logs: `kubectl logs <pod-name> -n bookstore`
- **File-based logs:**
  - API Server: `docker-compose exec api-server cat /logs/backend_logs.txt`
  - GKE: `kubectl exec -it deploy/backend -n bookstore -- cat /logs/backend_logs.txt`

### Shell Access
- **Docker Compose:**
  - Backend: `make shell-backend`
  - Frontend: `make shell-frontend`
  - Postgres: `make shell-db`
  - pgAdmin: `make shell-pgadmin`
- **Kubernetes/GKE:**
  - Backend: `kubectl exec -it deploy/backend -n bookstore -- sh`
  - Frontend: `kubectl exec -it deploy/frontend -n bookstore -- sh`
  - Postgres: `kubectl exec -it deploy/postgres -n bookstore -- sh`
  - pgAdmin: `kubectl exec -it deploy/pgadmin -n bookstore -- sh`

### Cleanup Commands
- **Docker Compose:**
  - Stop and remove all: `make down` or `docker-compose down -v`
  - Prune system/volumes: `make prune` or `docker system prune -f && docker volume prune -f`
- **Kubernetes:**
  - Delete dev resources: `make k8s-delete-dev`
  - Delete prod resources: `make k8s-delete-prod`
  - Delete namespace: `kubectl delete namespace bookstore`
- **GCP/GKE:**
  - Delete cluster, static IPs, and images via GCP Console or CLI (see GCP cleanup guide).

### Resetting Services
- **Database reset:**
  - Compose: `make db-reset`
- **Restart all services:**
  - Compose: `make restart`
  - K8s: `kubectl rollout restart deployment/backend -n bookstore`

### More Help
- Run `make help` to see all available commands.
- See the SSL/TLS section below for HTTPS and domain troubleshooting.

---

## 🔒 SSL/TLS and Domain Setup (GKE)

### Enabling HTTPS with GKE ManagedCertificate
- GKE supports Google-managed SSL certificates for your Ingress.
- To enable HTTPS:
  1. Acquire a domain (e.g., `yourdomain.com`).
  2. Edit `k8s/base/managed-certificate.yaml`:
     - Uncomment and set your domain:
       ```yaml
       spec:
         domains:
           - bookstore.yourdomain.com
       ```
  3. Edit `k8s/base/ingress.yaml`:
     - Uncomment domain-related annotations and set the `host` field:
       ```yaml
       annotations:
         kubernetes.io/ingress.global-static-ip-name: "bkmrk-static-ip"
         networking.gke.io/managed-certificates: "bookstore-certificate"
         cloud.google.com/app-protocols: '{"https":"HTTPS"}'
         networking.gke.io/v1beta1.FrontendConfig: "bkmrk-frontend-config"
       spec:
         rules:
           - host: bookstore.yourdomain.com
       ```
  4. Update your DNS provider:
     - Add an `A` record for `bookstore.yourdomain.com` pointing to your Ingress external IP.
  5. Apply the changes:
     ```sh
     kubectl apply -k k8s/overlays/gce-prod
     ```
  6. Wait for certificate provisioning (can take 10–30 min):
     ```sh
     kubectl describe managedcertificate bookstore-certificate -n bookstore
     ```

### How TLS/SSL Works (in brief)
- The GKE Ingress controller terminates TLS at the load balancer.
- Google manages the private key and certificate lifecycle.
- The TLS handshake ensures secure, encrypted communication between clients and your app.

### Troubleshooting SSL/Certificate Issues
- **Certificate not provisioned:**
  - Check status: `kubectl describe managedcertificate bookstore-certificate -n bookstore`
  - Ensure DNS is correct and propagated.
  - Wait for GKE to complete provisioning.
- **HTTPS not working:**
  - Ensure all annotations and domain fields are set correctly in your Ingress and certificate YAMLs.
  - Check that your DNS A record points to the Ingress external IP.
- **Force HTTPS:**
  - Use `FrontendConfig` to redirect HTTP to HTTPS (see `frontend-config.yaml`).
- **Testing:**
  - Use `curl -v https://bookstore.yourdomain.com` to debug SSL issues.

---

## 🌐 Environment Variables Reference

Below are all required environment variables for both local and cloud deployments. Set these in your `.env` file or as Kubernetes secrets/configmaps as appropriate.

### Database Configuration
- `DATABASE_URL` — PostgreSQL connection string (e.g., `postgresql://user:password@postgres:5432/bookstore`)
- `POSTGRES_DB` — Database name
- `POSTGRES_USER` — Database user
- `POSTGRES_PASSWORD` — Database password

### Backend Configuration
- `SECRET_KEY` — Secret key for JWT/auth (change in production!)
- `ACCESS_TOKEN_EXPIRE_MINUTES` — JWT token expiry (minutes)

### Redis Configuration
- `REDIS_URL` — Redis connection string (e.g., `redis://localhost:6379`)

### Frontend Configuration
- `NEXT_PUBLIC_API_URL` — Backend API URL for Next.js frontend (e.g., `http://localhost:8000`)
- `NEXT_PUBLIC_MCP_SERVER_URL` — MCP server URL (e.g., `http://localhost:8001`)
- `NEXT_PUBLIC_ANALYTICS_URL` — Analytics server URL (e.g., `http://localhost:8002`)

### PgAdmin Configuration
- `PGADMIN_DEFAULT_EMAIL` — pgAdmin login email
- `PGADMIN_DEFAULT_PASSWORD` — pgAdmin login password

### AI/ML & Vector DB Configuration
- `GEMINI_API_KEY` — Google Gemini API key
- `OPENAI_API_KEY` — OpenAI API key
- `ANTHROPIC_API_KEY` — Anthropic API key
- `COHERE_API_KEY` — Cohere API key
- `WEAVIATE_URL` — Weaviate vector DB URL (e.g., `http://weaviate:8080`)
- `WEAVIATE_API_KEY` — Weaviate API key (if needed)
- `MCP_SERVER_URL` — MCP server URL
- `ANALYTICS_SERVER_URL` — Analytics server URL

### Kaggle Data Loader
- `KAGGLE_USERNAME` — Kaggle username
- `KAGGLE_KEY` — Kaggle API key

### Monitoring & Observability
- `PROMETHEUS_ENABLED` — Enable Prometheus metrics (`true`/`false`)
- `OPENTELEMETRY_ENABLED` — Enable OpenTelemetry tracing (`true`/`false`)

### Logging
- `LOG_DIR` — Directory for backend logs (default: `/logs`)

---

**Set these variables in your `.env` file for local dev, or as Kubernetes secrets/configmaps for cloud. Never commit secrets to version control!**

---

## 🤖 AI API Keys: Which Are Required?

- `GEMINI_API_KEY` — **Required** for Gemini-powered AI features (recommendation engine, enrichment, etc.)
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY` — Only required if you enable those providers in your code. Leave blank if not used.

**Startup Check:**
- The backend will refuse to start if a required AI API key (e.g., `GEMINI_API_KEY`) is missing, and will log a clear error message.
- If you add more AI providers, add their keys to the required list in `main.py`.
