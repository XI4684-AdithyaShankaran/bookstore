#!/bin/bash

# Environment Testing Script
# Tests environment switching and validates configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

# Function to test environment file
test_environment_file() {
    local env_file=$1
    local env_name=$2
    
    print_status "INFO" "Testing $env_name environment ($env_file)"
    
    if [ ! -f "$env_file" ]; then
        print_status "ERROR" "Environment file $env_file not found"
        return 1
    fi
    
    # Check required variables
    local required_vars=(
        "DATABASE_URL"
        "SECRET_KEY"
        "NEXTAUTH_SECRET"
        "ENVIRONMENT"
        "DEBUG"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$env_file"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_status "SUCCESS" "All required variables present in $env_name"
    else
        print_status "ERROR" "Missing required variables in $env_name: ${missing_vars[*]}"
        return 1
    fi
    
    # Check environment-specific settings
    case $env_name in
        "local")
            if grep -q "DEBUG=true" "$env_file" && grep -q "localhost" "$env_file"; then
                print_status "SUCCESS" "Local environment configured correctly"
            else
                print_status "WARNING" "Local environment may not be configured optimally"
            fi
            ;;
        "dev")
            if grep -q "DEBUG=true" "$env_file" && grep -q "dev" "$env_file"; then
                print_status "SUCCESS" "Development environment configured correctly"
            else
                print_status "WARNING" "Development environment may not be configured optimally"
            fi
            ;;
        "prod")
            if grep -q "DEBUG=false" "$env_file" && grep -q "\${" "$env_file"; then
                print_status "SUCCESS" "Production environment configured correctly"
            else
                print_status "WARNING" "Production environment may not be configured optimally"
            fi
            ;;
    esac
}

# Function to test environment switching
test_environment_switching() {
    print_status "INFO" "Testing environment switching"
    
    local environments=("local" "dev" "prod")
    
    for env in "${environments[@]}"; do
        print_status "INFO" "Switching to $env environment"
        
        # Test make command
        if make env-switch ENV="$env" > /dev/null 2>&1; then
            print_status "SUCCESS" "Successfully switched to $env environment"
        else
            print_status "ERROR" "Failed to switch to $env environment"
            return 1
        fi
        
        # Verify .env file was created
        if [ -f ".env" ]; then
            print_status "SUCCESS" ".env file created for $env environment"
        else
            print_status "ERROR" ".env file not created for $env environment"
            return 1
        fi
        
        # Test environment-specific commands
        case $env in
            "local")
                if make dev > /dev/null 2>&1; then
                    print_status "SUCCESS" "Local development command works"
                else
                    print_status "WARNING" "Local development command may have issues"
                fi
                ;;
            "dev")
                if make k8s-apply-dev > /dev/null 2>&1; then
                    print_status "SUCCESS" "Development deployment command works"
                else
                    print_status "WARNING" "Development deployment command may have issues"
                fi
                ;;
            "prod")
                if make k8s-apply-prod > /dev/null 2>&1; then
                    print_status "SUCCESS" "Production deployment command works"
                else
                    print_status "WARNING" "Production deployment command may have issues"
                fi
                ;;
        esac
    done
}

# Function to test Docker integration
test_docker_integration() {
    print_status "INFO" "Testing Docker integration"
    
    local environments=("local" "dev" "prod")
    
    for env in "${environments[@]}"; do
        print_status "INFO" "Testing Docker with $env environment"
        
        # Copy environment file with correct naming
        if [ "$env" = "dev" ]; then
            cp "env.development" .env
        elif [ "$env" = "prod" ]; then
            cp "env.production" .env
        else
            cp "env.$env" .env
        fi
        
        # Test Docker Compose
        if docker-compose config > /dev/null 2>&1; then
            print_status "SUCCESS" "Docker Compose configuration valid for $env"
        else
            print_status "ERROR" "Docker Compose configuration invalid for $env"
            return 1
        fi
    done
}

# Function to test Kubernetes integration
test_kubernetes_integration() {
    print_status "INFO" "Testing Kubernetes integration"
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_status "WARNING" "kubectl not found, skipping Kubernetes tests"
        return 0
    fi
    
    # Test namespace creation
    if kubectl create namespace bookstore-test --dry-run=client -o yaml > /dev/null 2>&1; then
        print_status "SUCCESS" "Kubernetes namespace creation works"
    else
        print_status "WARNING" "Kubernetes namespace creation failed (kubectl may not be configured)"
    fi
    
    # Test secret creation
    if kubectl create secret generic test-secret --from-file=.env --dry-run=client -o yaml > /dev/null 2>&1; then
        print_status "SUCCESS" "Kubernetes secret creation works"
    else
        print_status "WARNING" "Kubernetes secret creation failed (kubectl may not be configured)"
    fi
}

# Function to test Git branch integration
test_git_branch_integration() {
    print_status "INFO" "Testing Git branch integration"
    
    local current_branch
    current_branch=$(git branch --show-current)
    print_status "INFO" "Current branch: $current_branch"
    
    # Check if we're on a valid environment branch
    case $current_branch in
        "main"|"dev"|"local")
            print_status "SUCCESS" "On valid environment branch: $current_branch"
            ;;
        *)
            print_status "WARNING" "Not on a standard environment branch: $current_branch"
            ;;
    esac
    
    # Check if .env file matches branch
    if [ -f ".env" ]; then
        local env_content
        env_content=$(head -1 .env 2>/dev/null || echo "")
        case $current_branch in
            "main")
                if echo "$env_content" | grep -q "production"; then
                    print_status "SUCCESS" "Production environment file matches main branch"
                else
                    print_status "WARNING" "Environment file may not match main branch"
                fi
                ;;
            "dev")
                if echo "$env_content" | grep -q "development"; then
                    print_status "SUCCESS" "Development environment file matches dev branch"
                else
                    print_status "WARNING" "Environment file may not match dev branch"
                fi
                ;;
            "local")
                if echo "$env_content" | grep -q "local"; then
                    print_status "SUCCESS" "Local environment file matches local branch"
                else
                    print_status "WARNING" "Environment file may not match local branch"
                fi
                ;;
        esac
    fi
}

# Main test function
main() {
    print_status "INFO" "Starting environment testing"
    
    # Test environment files
    test_environment_file "env.local" "local"
    test_environment_file "env.development" "dev"
    test_environment_file "env.production" "prod"
    
    # Test environment switching
    test_environment_switching
    
    # Test Docker integration
    test_docker_integration
    
    # Test Kubernetes integration
    test_kubernetes_integration
    
    # Test Git branch integration
    test_git_branch_integration
    
    print_status "SUCCESS" "Environment testing completed"
}

# Run main function
main "$@" 