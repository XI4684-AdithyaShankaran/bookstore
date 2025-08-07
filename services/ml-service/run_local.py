#!/usr/bin/env python3
"""
Local ML Service Runner
Runs the ML service locally without Docker for development
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def setup_environment():
    """Setup environment variables for local development"""
    env_vars = {
        'GEMINI_API_KEY': 'AIzaSyDd5LhOtk_eBobz7XBLB_vcJoYOTuYhUFM',
        'OPENAI_API_KEY': 'your-openai-key-here',
        'HUGGINGFACE_API_KEY': 'your-huggingface-key-here',
        'DATABASE_URL': 'postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db',
        'REDIS_URL': 'redis://localhost:6379',
        'WEAVIATE_URL': 'http://localhost:8080',
        'LOG_LEVEL': 'INFO',
        'PORT': '8003'
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
    """Run the ML service"""
    print("🚀 Starting ML Service...")
    print("📍 Service will be available at: http://localhost:8003")
    print("🔗 Health check: http://localhost:8003/health")
    print("📚 Recommendations: http://localhost:8003/recommendations")
    
    try:
        uvicorn.run(
            "app.mcp_server:app",
            host="0.0.0.0",
            port=8003,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 ML Service stopped")
    except Exception as e:
        print(f"❌ Failed to start ML service: {e}")

if __name__ == "__main__":
    print("🤖 ML Service Local Runner")
    print("=" * 40)
    
    # Setup environment
    setup_environment()
    
    # Install dependencies if needed
    if not install_dependencies():
        sys.exit(1)
    
    # Run the service
    run_service() 