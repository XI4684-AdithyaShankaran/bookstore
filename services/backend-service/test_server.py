#!/usr/bin/env python3
"""
Simple test script for the backend service
"""

import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    # Set basic environment variables for testing
    os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')
    os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development')
    os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
    os.environ.setdefault('GEMINI_API_KEY', 'dummy-key')
    
    print("🚀 Starting Backend Service for testing...")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 