#!/usr/bin/env python3
"""
API Gateway for Bkmrk'd Bookstore
Centralized routing, authentication, and monitoring
"""

import os
import logging
import time
import json
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import httpx
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Service URLs
SERVICE_URLS = {
    "backend": os.getenv("BACKEND_SERVICE_URL", "http://backend-service:8001"),
    "recommendation": os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation-engine:8002"),
    "ml": os.getenv("ML_SERVICE_URL", "http://ml-service:8003"),
    "observability": os.getenv("OBSERVABILITY_SERVICE_URL", "http://observability-service:8004"),
    "etl": os.getenv("ETL_SERVICE_URL", "http://etl-pipeline:8005")
}

# Redis client for caching and rate limiting
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global redis_client
    
    # Startup
    logger.info("🚀 Starting Bkmrk'd API Gateway...")
    try:
        # Initialize Redis connection
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis connection established")
        
        logger.info("✅ API Gateway started successfully")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🔄 Shutting down API Gateway...")
    try:
        if redis_client:
            redis_client.close()
            logger.info("✅ Redis connection closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")
    
    logger.info("👋 API Gateway shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="Bkmrk'd API Gateway",
    description="API gateway for Bkmrk'd Bookstore",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)

# Request/Response models
class GatewayRequest(BaseModel):
    service: str = Field(..., description="Target service name")
    endpoint: str = Field(..., description="Service endpoint")
    method: str = Field("GET", description="HTTP method")
    data: Optional[Dict[str, Any]] = Field(None, description="Request data")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")

class GatewayResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    service: str
    endpoint: str
    response_time: float

# Authentication middleware
async def get_current_user(request: Request):
    """Extract and validate JWT token"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        
        # Validate token with backend service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICE_URLS['backend']}/api/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return None

# Service routing
async def route_request(
    service: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Route request to appropriate microservice"""
    
    if service not in SERVICE_URLS:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")
    
    service_url = SERVICE_URLS[service]
    full_url = f"{service_url}{endpoint}"
    
    # Prepare headers
    request_headers = {
        "Content-Type": "application/json",
        "User-Agent": "Bkmrk'd-API-Gateway/1.0.0"
    }
    
    if headers:
        request_headers.update(headers)
    
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(full_url, headers=request_headers)
            elif method.upper() == "POST":
                response = await client.post(full_url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = await client.put(full_url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await client.delete(full_url, headers=request_headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
            
            response_time = time.time() - start_time
            
            # Log request
            logger.info(f"Service: {service}, Endpoint: {endpoint}, Method: {method}, Status: {response.status_code}, Time: {response_time:.3f}s")
            
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            
            return {
                "success": True,
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "service": service,
                "endpoint": endpoint,
                "response_time": response_time
            }
            
    except httpx.TimeoutException:
        response_time = time.time() - start_time
        logger.error(f"Timeout for {service}:{endpoint} after {response_time:.3f}s")
        raise HTTPException(status_code=504, detail=f"Service {service} timeout")
        
    except httpx.RequestError as e:
        response_time = time.time() - start_time
        logger.error(f"Request error for {service}:{endpoint}: {e}")
        raise HTTPException(status_code=503, detail=f"Service {service} unavailable")
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Unexpected error for {service}:{endpoint}: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

# Cache middleware
async def get_cached_response(cache_key: str) -> Optional[Dict]:
    """Get cached response from Redis"""
    if not redis_client:
        return None
    
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    
    return None

async def set_cached_response(cache_key: str, data: Dict, ttl: int = 300):
    """Set cached response in Redis"""
    if not redis_client:
        return
    
    try:
        redis_client.setex(cache_key, ttl, json.dumps(data))
    except Exception as e:
        logger.warning(f"Cache set error: {e}")

# Health check endpoint
@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    """Health check endpoint"""
    try:
        # Check all services
        service_status = {}
        
        for service_name, service_url in SERVICE_URLS.items():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{service_url}/health")
                    service_status[service_name] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds()
                    }
            except Exception as e:
                service_status[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return {
            "status": "healthy",
            "service": "Bkmrk'd API Gateway",
            "version": "1.0.0",
            "timestamp": time.time(),
            "services": service_status
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gateway unhealthy"
        )

# Generic routing endpoint
@app.post("/api/gateway/route")
@limiter.limit("1000/minute")
async def route_generic_request(
    request: GatewayRequest,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Generic routing endpoint for all services"""
    
    # Generate cache key
    cache_key = f"gateway:{request.service}:{request.endpoint}:{request.method}:{hash(str(request.data))}"
    
    # Check cache for GET requests
    if request.method.upper() == "GET":
        cached = await get_cached_response(cache_key)
        if cached:
            return GatewayResponse(**cached)
    
    # Route request
    result = await route_request(
        service=request.service,
        endpoint=request.endpoint,
        method=request.method,
        data=request.data
    )
    
    # Cache successful GET responses
    if request.method.upper() == "GET" and result["success"]:
        await set_cached_response(cache_key, result)
    
    return GatewayResponse(**result)

# Backend service routes
@app.get("/api/books")
@limiter.limit("1000/minute")
async def get_books(
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None
):
    """Get books from backend service"""
    params = {k: v for k, v in locals().items() if v is not None}
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    
    return await route_request(
        service="backend",
        endpoint=f"/api/books?{query_string}",
        method="GET"
    )

@app.get("/api/books/{book_id}")
@limiter.limit("1000/minute")
async def get_book(book_id: int):
    """Get book by ID from backend service"""
    return await route_request(
        service="backend",
        endpoint=f"/api/books/{book_id}",
        method="GET"
    )

# Recommendation service routes
@app.post("/api/recommendations")
@limiter.limit("500/minute")
async def get_recommendations(request: Dict[str, Any]):
    """Get recommendations from recommendation engine"""
    return await route_request(
        service="recommendation",
        endpoint="/recommendations",
        method="POST",
        data=request
    )

@app.get("/api/recommendations/wishlist")
@limiter.limit("500/minute")
async def get_wishlist_recommendations(
    user_id: int,
    limit: int = 5
):
    """Get wishlist recommendations"""
    return await route_request(
        service="recommendation",
        endpoint=f"/recommendations/wishlist?user_id={user_id}&limit={limit}",
        method="GET"
    )

@app.get("/api/recommendations/trending")
@limiter.limit("500/minute")
async def get_trending_recommendations(limit: int = 10):
    """Get trending recommendations"""
    return await route_request(
        service="recommendation",
        endpoint=f"/recommendations/trending?limit={limit}",
        method="GET"
    )

# ML service routes
@app.post("/api/ml/embed")
@limiter.limit("200/minute")
async def embed_text(request: Dict[str, Any]):
    """Embed text using ML service"""
    return await route_request(
        service="ml",
        endpoint="/embed",
        method="POST",
        data=request
    )

@app.post("/api/ml/search")
@limiter.limit("200/minute")
async def vector_search(request: Dict[str, Any]):
    """Vector search using ML service"""
    return await route_request(
        service="ml",
        endpoint="/search",
        method="POST",
        data=request
    )

# Observability service routes
@app.get("/api/analytics/metrics")
@limiter.limit("100/minute")
async def get_analytics_metrics():
    """Get analytics metrics"""
    return await route_request(
        service="observability",
        endpoint="/analytics/metrics",
        method="GET"
    )

# User management routes (backend service)
@app.get("/api/users/me")
@limiter.limit("100/minute")
async def get_current_user_info(current_user: Optional[Dict] = Depends(get_current_user)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return await route_request(
        service="backend",
        endpoint="/api/users/me",
        method="GET"
    )

# Cart routes (backend service)
@app.get("/api/cart")
@limiter.limit("100/minute")
async def get_cart(current_user: Optional[Dict] = Depends(get_current_user)):
    """Get user cart"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return await route_request(
        service="backend",
        endpoint="/api/cart",
        method="GET"
    )

@app.post("/api/cart/items")
@limiter.limit("50/minute")
async def add_to_cart(
    book_id: int,
    quantity: int = 1,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Add item to cart"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return await route_request(
        service="backend",
        endpoint="/api/cart/items",
        method="POST",
        data={"book_id": book_id, "quantity": quantity}
    )

# Search endpoint
@app.get("/api/search")
@limiter.limit("200/minute")
async def search_books(q: str, limit: int = 20):
    """Search books"""
    return await route_request(
        service="backend",
        endpoint=f"/api/search?q={q}&limit={limit}",
        method="GET"
    )

# Error handling middleware
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "service": "api-gateway",
            "timestamp": time.time()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal gateway error",
            "service": "api-gateway",
            "timestamp": time.time()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    ) 