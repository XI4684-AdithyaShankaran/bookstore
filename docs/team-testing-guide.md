# Team Testing Guide

## Overview

This guide helps your team test and validate the environment-specific setup with git branches. Follow these steps to ensure everything works correctly across all environments.

## Prerequisites

Before testing, ensure you have:
- Docker and Docker Compose installed
- kubectl configured (for Kubernetes testing)
- Access to the GitHub repository
- Required API keys and credentials

## Testing Checklist

### ✅ 1. Environment File Validation

Test that all environment files are properly configured:

```bash
# Test environment files
make test-environments

# Validate current environment
make validate-env
```

**Expected Results:**
- All environment files should exist (`env.local`, `env.development`, `env.production`)
- Required variables should be present in each file
- Environment-specific settings should be correct

### ✅ 2. Git Branch Testing

Test environment switching with git branches:

```bash
# Test local environment
git checkout local
make env-local
make validate-env

# Test development environment
git checkout dev
make env-dev
make validate-env

# Test production environment
git checkout main
make env-prod
make validate-env
```

**Expected Results:**
- Each branch should have the correct `.env` file
- Environment variables should match the branch purpose
- No conflicts between environments

### ✅ 3. Docker Integration Testing

Test Docker Compose with different environments:

```bash
# Test local environment
git checkout local
make env-local
docker-compose config

# Test development environment
git checkout dev
make env-dev
docker-compose config

# Test production environment
git checkout main
make env-prod
docker-compose config
```

**Expected Results:**
- Docker Compose should validate successfully
- Environment variables should be properly injected
- No configuration errors

### ✅ 4. Kubernetes Integration Testing

Test Kubernetes deployment with different environments:

```bash
# Test development deployment
git checkout dev
make env-dev
make k8s-apply-dev

# Test production deployment
git checkout main
make env-prod
make k8s-apply-prod
```

**Expected Results:**
- Kubernetes manifests should apply successfully
- Secrets should be created properly
- Services should be accessible

### ✅ 5. CI/CD Pipeline Testing

Test GitHub Actions workflows:

```bash
# Push to local branch (triggers local CI/CD)
git checkout local
git push origin local

# Push to dev branch (triggers development CI/CD)
git checkout dev
git push origin dev

# Push to main branch (triggers production CI/CD)
git checkout main
git push origin main
```

**Expected Results:**
- GitHub Actions should run successfully
- Docker images should be built and pushed
- Security scans should pass
- Tests should pass

## Team Testing Scenarios

### Scenario 1: New Developer Setup

**Objective:** Test the onboarding process for a new team member

**Steps:**
1. Clone the repository
2. Switch to local branch
3. Set up local environment
4. Start development server
5. Run tests

```bash
git clone <repository-url>
cd bookstore
git checkout local
make env-local
make dev
make test
```

**Success Criteria:**
- Local environment starts without errors
- All tests pass
- Development server is accessible

### Scenario 2: Feature Development Workflow

**Objective:** Test the complete development workflow

**Steps:**
1. Create feature branch from local
2. Develop and test locally
3. Merge to dev branch
4. Test in development environment
5. Merge to main branch
6. Deploy to production

```bash
# Start feature development
git checkout local
git checkout -b feature/new-feature
# ... develop and test ...
git push origin feature/new-feature

# Merge to dev
git checkout dev
git merge feature/new-feature
git push origin dev

# Merge to main
git checkout main
git merge dev
git push origin main
```

**Success Criteria:**
- Feature works in all environments
- No environment-specific issues
- Deployment succeeds in all environments

### Scenario 3: Environment-Specific Configuration

**Objective:** Test environment-specific settings

**Steps:**
1. Test local environment settings
2. Test development environment settings
3. Test production environment settings

```bash
# Test local settings
git checkout local
make env-local
grep "DEBUG=" .env  # Should be true
grep "localhost" .env  # Should be present

# Test dev settings
git checkout dev
make env-dev
grep "DEBUG=" .env  # Should be true
grep "dev" .env  # Should be present

# Test prod settings
git checkout main
make env-prod
grep "DEBUG=" .env  # Should be false
grep "\${" .env  # Should be present (env vars)
```

**Success Criteria:**
- Each environment has appropriate settings
- No hardcoded production values in development
- Environment variables are properly configured

### Scenario 4: Secrets Management

**Objective:** Test secrets handling across environments

**Steps:**
1. Test local secrets (placeholder values)
2. Test development secrets (test values)
3. Test production secrets (environment variables)

```bash
# Test local secrets
git checkout local
make env-local
grep "your_" .env  # Should find placeholder values

# Test dev secrets
git checkout dev
make env-dev
grep "dev_" .env  # Should find dev-prefixed values

# Test prod secrets
git checkout main
make env-prod
grep "\${" .env  # Should find environment variables
```

**Success Criteria:**
- Local environment uses safe placeholder values
- Development environment uses test credentials
- Production environment uses environment variables

## Troubleshooting Common Issues

### Issue 1: Environment File Not Found

**Symptoms:** `make env-switch` fails with "file not found"

**Solution:**
```bash
# Check if environment files exist
ls -la env.*

# Create missing files if needed
cp env.local env.development  # if missing
cp env.local env.production   # if missing
```

### Issue 2: Docker Compose Configuration Errors

**Symptoms:** `docker-compose config` fails

**Solution:**
```bash
# Check environment file
cat .env

# Validate Docker Compose file
docker-compose config --quiet
```

### Issue 3: Kubernetes Deployment Failures

**Symptoms:** `make k8s-apply-*` fails

**Solution:**
```bash
# Check kubectl configuration
kubectl config current-context

# Check namespace
kubectl get namespaces

# Check secrets
kubectl get secrets -n bookstore-dev
```

### Issue 4: GitHub Actions Failures

**Symptoms:** CI/CD pipeline fails

**Solution:**
1. Check GitHub repository settings
2. Verify branch protection rules
3. Check required status checks
4. Review workflow logs

## Performance Testing

### Load Testing

Test each environment with different load levels:

```bash
# Local load testing
git checkout local
make env-local
make dev
# Use tools like Apache Bench or wrk to test

# Development load testing
git checkout dev
make env-dev
make k8s-apply-dev
# Test with production-like load

# Production load testing
git checkout main
make env-prod
make k8s-apply-prod
# Test with real production load
```

### Security Testing

Test security configurations:

```bash
# Test local security (should be relaxed)
git checkout local
make env-local
# Verify debug mode is enabled
# Verify rate limiting is disabled

# Test dev security (should be moderate)
git checkout dev
make env-dev
# Verify debug mode is enabled
# Verify rate limiting is enabled

# Test prod security (should be strict)
git checkout main
make env-prod
# Verify debug mode is disabled
# Verify rate limiting is enabled
# Verify HTTPS is enforced
```

## Reporting

After completing all tests, create a test report:

```bash
# Generate test report
make test-environments > test-report.txt 2>&1
make validate-env >> test-report.txt 2>&1

# Review results
cat test-report.txt
```

**Report Template:**
```
Environment Testing Report
=========================

Date: [Date]
Tester: [Name]
Environment: [local/dev/prod]

✅ Environment Files: [PASS/FAIL]
✅ Git Branches: [PASS/FAIL]
✅ Docker Integration: [PASS/FAIL]
✅ Kubernetes Integration: [PASS/FAIL]
✅ CI/CD Pipeline: [PASS/FAIL]
✅ Secrets Management: [PASS/FAIL]

Issues Found:
- [List any issues]

Recommendations:
- [List recommendations]
```

## Continuous Testing

Set up automated testing:

```bash
# Add to your daily workflow
make test-environments
make validate-env

# Add to pre-commit hooks
# Add to CI/CD pipeline
# Add to deployment pipeline
```

This ensures your environment setup remains reliable and secure. 