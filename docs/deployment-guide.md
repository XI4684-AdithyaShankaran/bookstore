# 🚀 Bkmrk'd - Complete Deployment Guide

## 📋 Project Overview

**Bkmrk'd** is a modern, full-stack bookstore application built with Next.js frontend and FastAPI backend, featuring AI-powered book recommendations, infinite scrolling, and custom bookshelves.

### 🏗️ Architecture
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS
- **Backend**: FastAPI + Python + SQLAlchemy
- **Database**: PostgreSQL + Redis (caching)
- **AI/ML**: Gemini API + Weaviate (vector DB) + MCP Server
- **Containerization**: Docker + Docker Compose
- **Cloud Deployment**: Kubernetes (GKE) + Google Cloud Platform

---

## 📋 Prerequisites

### 🖥️ Local Development
- **Docker & Docker Compose** (latest version)
- **Node.js** 20+ 
- **Python** 3.11+
- **Git** (for version control)
- **Make** (for build automation)

### ☁️ Cloud Deployment (GCP)
- **Google Cloud SDK** installed and configured
- **kubectl** configured for GKE
- **Docker** for building images
- **Domain name** (optional, for HTTPS)

### 🔑 Required API Keys
- **Google Gemini API** (required for AI features)
- **Kaggle API** (for book data loading)
- **Google OAuth** (for authentication)

---

## 🧹 Cleanup & Preparation

### Local Cleanup
```bash
# Stop all running containers
docker-compose down -v

# Remove all images and volumes
docker system prune -a -f
docker volume prune -f

# Clean npm cache
cd frontend && rm -rf node_modules package-lock.json
cd ..

# Clean Python cache
cd backend && rm -rf venv __pycache__ *.pyc
cd ..
```

### GCP Cleanup (if redeploying)
```bash
# Delete existing resources
kubectl delete namespace bookstore --ignore-not-found=true
gcloud compute addresses delete bkmrk-static-ip --region=us-central1 --quiet
gcloud container clusters delete bookstore-cluster --zone=us-central1-a --quiet

# Clean up images
gcloud container images delete gcr.io/bookstore-project-464717/bookstore-backend:latest --quiet
gcloud container images delete gcr.io/bookstore-project-464717/bookstore-frontend:latest --quiet
```

---

## 🚀 Local Development Setup

### Step 1: Environment Configuration
```bash
# Update .env with your configuration
# Required: SECRET_KEY, GEMINI_API_KEY, KAGGLE_USERNAME, KAGGLE_KEY
```

### Step 2: One-Command Setup
```bash
# Complete setup (dependencies + services)
make setup

# Or step-by-step:
make install          # Install all dependencies
make env-dev         # Set development environment
make up              # Start all services
```

### Step 3: Verify Setup
```bash
# Check all services are running
docker-compose ps

# View logs
make logs

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:3000
```

### Step 4: Load Sample Data
```bash
# Load Kaggle book data
docker build -f backend/Dockerfile.kaggleloader -t bkmrk-kaggle-loader backend/
docker run --env-file .env bkmrk-kaggle-loader
```

---

## ☁️ Google Cloud Platform Setup

### Step 1: GCP Project Setup
```bash
# Set your project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Authentication & IAM
```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Create service account for deployment
gcloud iam service-accounts create bookstore-deployer \
    --display-name="Bookstore Deployer"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bookstore-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/container.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:bookstore-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

### Step 3: Artifact Registry
```bash
# Create repository for Docker images
gcloud artifacts repositories create bookstore-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="Bookstore Docker Repository"
```

### Step 4: VPC & Networking
```bash
# Create VPC network
gcloud compute networks create bookstore-vpc \
    --subnet-mode=auto

# Create firewall rules
gcloud compute firewall-rules create bookstore-allow-http \
    --network=bookstore-vpc \
    --allow=tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0
```

### Step 5: GKE Cluster
```bash
# Create GKE cluster
gcloud container clusters create bookstore-cluster \
    --zone=us-central1-a \
    --network=bookstore-vpc \
    --num-nodes=2 \
    --machine-type=e2-standard-2 \
    --enable-autoscaling \
    --min-nodes=1 \
    --max-nodes=5

# Get credentials
gcloud container clusters get-credentials bookstore-cluster --zone=us-central1-a
```

### Step 6: Static IP
```bash
# Reserve static IP for Ingress
gcloud compute addresses create bkmrk-static-ip \
    --region=us-central1
```

---

## 🐳 Docker Image Building & Pushing

### Step 1: Build Images
```bash
# Build backend image
docker build -f backend/Dockerfile -t gcr.io/$PROJECT_ID/bookstore-backend:latest backend/

# Build frontend image
docker build -f frontend/Dockerfile -t gcr.io/$PROJECT_ID/bookstore-frontend:latest frontend/

# Build Kaggle loader image
docker build -f backend/Dockerfile.kaggleloader -t gcr.io/$PROJECT_ID/bookstore-kaggle-loader:latest backend/
```

### Step 2: Push to Registry
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Push images
docker push gcr.io/$PROJECT_ID/bookstore-backend:latest
docker push gcr.io/$PROJECT_ID/bookstore-frontend:latest
docker push gcr.io/$PROJECT_ID/bookstore-kaggle-loader:latest
```

---

## ☸️ Kubernetes Deployment

### Step 1: Create Namespace
```bash
# Apply base configuration
kubectl apply -k k8s/base/

# Verify namespace creation
kubectl get namespace bookstore
```

### Step 2: Configure Secrets
```bash
# Create secrets from your .env file
kubectl create secret generic bookstore-secrets \
    --from-file=.env \
    -n bookstore

# Or create individual secrets
kubectl create secret generic database-secret \
    --from-literal=DATABASE_URL="postgresql://user:password@postgres:5432/bookstore" \
    -n bookstore

kubectl create secret generic ai-secret \
    --from-literal=GEMINI_API_KEY="your-gemini-key" \
    --from-literal=KAGGLE_USERNAME="your-kaggle-username" \
    --from-literal=KAGGLE_KEY="your-kaggle-key" \
    -n bookstore
```

### Step 3: Deploy Services
```bash
# Deploy all services
kubectl apply -k k8s/overlays/gce-prod/

# Check deployment status
kubectl get pods -n bookstore
kubectl get services -n bookstore
kubectl get ingress -n bookstore
```

### Step 4: Load Data
```bash
# Run Kaggle data loader job
kubectl apply -f k8s/base/kaggle-loader-job.yaml

# Monitor job progress
kubectl logs job/kaggle-loader -n bookstore -f
```

---

## 🌐 Access & Monitoring

### Get External IP
```bash
# Get Ingress external IP
kubectl get ingress bookstore-ingress -n bookstore -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Or use this command
EXTERNAL_IP=$(kubectl get ingress bookstore-ingress -n bookstore -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Access your app at: http://$EXTERNAL_IP"
```

### Health Checks
```bash
# Backend health
curl http://$EXTERNAL_IP/api/health

# Frontend
curl http://$EXTERNAL_IP

# Database connection
kubectl exec -it deploy/postgres -n bookstore -- psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

### Monitoring & Logs
```bash
# View all logs
kubectl logs -l app=backend -n bookstore
kubectl logs -l app=frontend -n bookstore

# Real-time logs
kubectl logs -f deploy/backend -n bookstore

# Resource usage
kubectl top pods -n bookstore
kubectl top nodes
```

---

## 🔄 Rollout Management

### Blue-Green Deployment
```bash
# Update image tag
kubectl set image deployment/backend backend=gcr.io/$PROJECT_ID/bookstore-backend:v2.0.0 -n bookstore

# Monitor rollout
kubectl rollout status deployment/backend -n bookstore

# Rollback if needed
kubectl rollout undo deployment/backend -n bookstore
```

### Canary Deployment
```bash
# Deploy canary version
kubectl apply -f k8s/overlays/canary/

# Gradually increase traffic
kubectl patch ingress bookstore-ingress -n bookstore -p '{"spec":{"rules":[{"http":{"paths":[{"path":"/","backend":{"serviceName":"backend-canary","servicePort":8000}}]}}]}}'
```

---

## 🔒 Security & SSL/TLS

### Domain Setup (Optional)
```bash
# Update ingress with your domain
kubectl patch ingress bookstore-ingress -n bookstore -p '{"spec":{"rules":[{"host":"bookstore.yourdomain.com"}]}}'

# Configure DNS
# Add A record: bookstore.yourdomain.com -> $EXTERNAL_IP
```

### SSL Certificate
```bash
# Apply managed certificate
kubectl apply -f k8s/base/managed-certificate.yaml

# Check certificate status
kubectl describe managedcertificate bookstore-certificate -n bookstore
```

---

## 🛠️ Troubleshooting

### Common Issues

**Pods stuck in Pending:**
```bash
kubectl describe pod <pod-name> -n bookstore
kubectl get events -n bookstore
```

**Service not accessible:**
```bash
kubectl get endpoints -n bookstore
kubectl describe service <service-name> -n bookstore
```

**Database connection issues:**
```bash
kubectl exec -it deploy/postgres -n bookstore -- psql -U $POSTGRES_USER -d $POSTGRES_DB
```

**Image pull errors:**
```bash
kubectl describe pod <pod-name> -n bookstore
# Check if image exists in registry
gcloud container images list-tags gcr.io/$PROJECT_ID/bookstore-backend
```

### Debug Commands
```bash
# Shell access to pods
kubectl exec -it deploy/backend -n bookstore -- sh
kubectl exec -it deploy/frontend -n bookstore -- sh

# Port forwarding for local access
kubectl port-forward svc/backend 8000:8000 -n bookstore
kubectl port-forward svc/frontend 3000:3000 -n bookstore

# View logs with timestamps
kubectl logs deploy/backend -n bookstore --timestamps
```

---

## 📊 Performance & Scaling

### Horizontal Pod Autoscaling
```bash
# Check HPA status
kubectl get hpa -n bookstore

# Scale manually if needed
kubectl scale deployment backend --replicas=5 -n bookstore
```

### Resource Monitoring
```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View resource usage
kubectl top pods -n bookstore
kubectl top nodes
```

---

## 🧪 Testing

### Local Testing
```bash
# Run frontend tests
cd frontend && npm test

# Run backend tests
cd backend && python -m pytest

# Integration tests
make test-integration
```

### Cloud Testing
```bash
# Test endpoints
curl -X GET http://$EXTERNAL_IP/api/books
curl -X POST http://$EXTERNAL_IP/api/auth/login -H "Content-Type: application/json" -d '{"username":"test","password":"test"}'

# Load testing
kubectl run load-test --image=busybox --rm -it --restart=Never -- wget -O- http://backend:8000/api/health
```

---

## 📚 Additional Resources

### Useful Commands
```bash
# Quick status check
make status

# Update dependencies only
make update-deps

# Update middleware configuration
make update-middleware

# Quick update (deps + middleware)
make quick-update

# View all available commands
make help
```

### Documentation Files
- `README.md` - Project overview and quick start
- `docs/blueprint.md` - Feature specifications and design
- `Makefile` - Build automation commands
- `k8s/` - Kubernetes deployment configurations

### Support
- Check logs: `make logs` or `kubectl logs`
- View status: `make status` or `kubectl get pods`
- Shell access: `make shell-backend` or `kubectl exec`
- Clean restart: `make restart` or `kubectl rollout restart`

---

## 🎯 Next Steps

1. **Customize Configuration**: Update environment variables for your specific needs
2. **Add Monitoring**: Set up Prometheus/Grafana for production monitoring
3. **Implement CI/CD**: Add GitHub Actions or Cloud Build for automated deployments
4. **Security Hardening**: Implement network policies and RBAC
5. **Backup Strategy**: Set up automated database backups
6. **Domain & SSL**: Configure custom domain with SSL certificate

---

## 🔧 Environment Variables Reference

### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/bookstore
POSTGRES_DB=bookstore
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Backend
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://redis:6379

# AI/ML
GEMINI_API_KEY=your-gemini-api-key
KAGGLE_USERNAME=your-kaggle-username
KAGGLE_KEY=your-kaggle-api-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_SECRET=your-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
```

### Optional Variables
```bash
# Monitoring
PROMETHEUS_ENABLED=true
OPENTELEMETRY_ENABLED=true

# Logging
LOG_DIR=/logs
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=*
ALLOWED_HOSTS=*
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100
```

---

*This guide covers both local development and cloud deployment scenarios. Choose the path that best fits your needs!* 