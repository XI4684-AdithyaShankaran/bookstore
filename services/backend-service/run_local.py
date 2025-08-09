#!/usr/bin/env python3
"""
Local Backend Service Runner
Runs the backend service locally without Docker for development
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def setup_environment():
    """Setup environment variables for local development"""
    env_vars = {
        'DATABASE_URL': 'postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db',
        'REDIS_URL': 'redis://localhost:6379',
        'ML_SERVICE_URL': 'http://localhost:8003',
        'RECOMMENDATION_SERVICE_URL': 'http://localhost:8002',
        'LOG_LEVEL': 'INFO',
        'PORT': '8000'
    }
    
    for key, value in env_vars.items():
        if key not in os.environ:
            os.environ[key] = value
            print(f"✅ Set {key}")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def run_service():
    """Run the backend service"""
    print("🚀 Starting Backend Service...")
    print("📍 Service will be available at: http://localhost:8000")
    print("🔗 Health check: http://localhost:8000/health")
    print("📚 Books API: http://localhost:8000/api/books")
    print("🔍 Search API: http://localhost:8000/api/search")
    
    try:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Backend Service stopped")
    except Exception as e:
        print(f"❌ Failed to start backend service: {e}")

if __name__ == "__main__":
    print("🏗️ Backend Service Local Runner")
    print("=" * 40)
    
    # Setup environment
    setup_environment()
    
    # Install dependencies if needed
    if not install_dependencies():
        sys.exit(1)
    
    # Run the service
    run_service() 