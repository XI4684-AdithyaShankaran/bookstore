# Environment Configuration Guide

## Overview

This project uses a **branch-based environment strategy** with three distinct environments:

- **`main` branch** → Production environment
- **`dev` branch** → Development/Staging environment  
- **`local` branch** → Local development environment

## Environment Files

Each environment has its own configuration file:

| Environment | File | Branch | Purpose |
|-------------|------|--------|---------|
| **Production** | `env.production` | `main` | Live production environment |
| **Development** | `env.development` | `dev` | Staging and testing environment |
| **Local** | `env.local` | `local` | Local development environment |

## Quick Start

### 1. Switch to Local Development
```bash
# Switch to local branch
git checkout local

# Activate local environment
make env-local

# Start development
make dev
```

### 2. Switch to Development Environment
```bash
# Switch to dev branch
git checkout dev

# Activate development environment
make env-dev

# Deploy to development
make k8s-apply-dev
```

### 3. Switch to Production Environment
```bash
# Switch to main branch
git checkout main

# Activate production environment
make env-prod

# Deploy to production
make k8s-apply-prod
```

## Environment Management Commands

### Make Commands
```bash
# Set up specific environments
make env-local    # Local development
make env-dev      # Development environment
make env-prod     # Production environment

# Switch environments dynamically
make env-switch ENV=local
make env-switch ENV=dev
make env-switch ENV=prod
```

### Manual Environment Switching
```bash
# Copy environment file to .env
cp env.local .env      # Local development
cp env.development .env # Development environment
cp env.production .env  # Production environment
```

## Environment-Specific Configurations

### Local Development (`env.local`)
- **Database**: `localhost:5432`
- **Redis**: `localhost:6379`
- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Debug**: `true`
- **Analytics**: `false`
- **Rate Limiting**: `false`

### Development Environment (`env.development`)
- **Database**: `dev-db.bookstore.com:5432`
- **Redis**: `dev-redis.bookstore.com:6379`
- **Frontend**: `https://dev.bookstore.com`
- **Backend**: `https://dev-api.bookstore.com`
- **Debug**: `true`
- **Analytics**: `true`
- **Rate Limiting**: `true`

### Production Environment (`env.production`)
- **Database**: Environment variables (K8s secrets)
- **Redis**: Environment variables (K8s secrets)
- **Frontend**: Environment variables
- **Backend**: Environment variables
- **Debug**: `false`
- **Analytics**: `true`
- **Rate Limiting**: `true`

## Git Workflow

### Branch Strategy
```
main (production)
├── dev (development)
└── local (local development)
```

### Development Workflow
1. **Local Development**: Work on `local` branch
2. **Testing**: Merge to `dev` branch for testing
3. **Production**: Merge to `main` branch for deployment

### Environment-Specific Commits
```bash
# Local development
git checkout local
git add env.local
git commit -m "Update local environment config"

# Development environment
git checkout dev
git add env.development
git commit -m "Update development environment config"

# Production environment
git checkout main
git add env.production
git commit -m "Update production environment config"
```

## Security Considerations

### Sensitive Data Handling
- **Local**: Placeholder values for development
- **Development**: Test credentials and API keys
- **Production**: Environment variables and Kubernetes secrets

### Environment Variables
- **Local**: Hardcoded values for easy setup
- **Development**: Semi-hardcoded with dev prefixes
- **Production**: All sensitive values use `${VARIABLE_NAME}` format

### Kubernetes Integration
```bash
# Create secrets from environment files
kubectl create secret generic bookstore-secrets \
  --from-file=.env \
  --namespace=bookstore

# Apply environment-specific configurations
kubectl apply -f k8s/overlays/dev/
kubectl apply -f k8s/overlays/prod/
```

## Docker Integration

### Environment File Usage
```bash
# Use specific environment file
docker-compose --env-file env.local up -d
docker-compose --env-file env.development up -d
docker-compose --env-file env.production up -d
```

### Docker Compose Configuration
```yaml
# docker-compose.yml
services:
  backend:
    env_file:
      - .env  # Uses the current .env file
```

## Troubleshooting

### Common Issues

1. **Environment not switching**
   ```bash
   # Check current .env file
   head -5 .env
   
   # Force environment switch
   make env-switch ENV=local
   ```

2. **Docker not picking up changes**
   ```bash
   # Rebuild with new environment
   docker-compose down
   make env-switch ENV=local
   docker-compose up --build -d
   ```

3. **Kubernetes secrets mismatch**
   ```bash
   # Update secrets from current .env
   kubectl delete secret bookstore-secrets
   kubectl create secret generic bookstore-secrets --from-file=.env
   ```

### Environment Validation
```bash
# Validate environment variables
make validate-env

# Check environment-specific settings
grep "ENVIRONMENT=" .env
grep "DEBUG=" .env
```

## Best Practices

### 1. Environment Isolation
- Never commit actual production secrets
- Use different API keys for each environment
- Separate databases for each environment

### 2. Configuration Management
- Keep environment files in version control
- Use environment variables for sensitive data
- Document all configuration changes

### 3. Deployment Strategy
- Test in development before production
- Use blue-green deployments for production
- Monitor environment-specific metrics

### 4. Security
- Rotate secrets regularly
- Use least privilege access
- Audit environment access

## Migration from Old Setup

If migrating from the old `env.example` setup:

1. **Backup current configuration**
   ```bash
   cp .env .env.backup
   ```

2. **Switch to new environment**
   ```bash
   make env-local  # or env-dev, env-prod
   ```

3. **Update with your specific values**
   ```bash
   # Edit .env with your actual API keys and configuration
   nano .env
   ```

4. **Test the new setup**
   ```bash
   make dev
   ```

## Support

For environment-related issues:
1. Check the troubleshooting section above
2. Verify your environment file is correct
3. Ensure Docker/Kubernetes is using the right environment
4. Check logs for environment-specific errors 