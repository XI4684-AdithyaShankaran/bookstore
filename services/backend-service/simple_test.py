#!/usr/bin/env python3
"""
Minimal test version of the backend service
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-development')
os.environ.setdefault('GEMINI_API_KEY', 'dummy-key')

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simple lifespan manager"""
    print("🚀 Starting simple test API...")
    yield
    print("🔄 Shutting down...")

app = FastAPI(title="Simple Test API", lifespan=lifespan)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Simple Test API",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Hello from Simple Test API!"}

if __name__ == "__main__":
    print("🚀 Starting Simple Test API...")
    uvicorn.run(
        "simple_test:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 