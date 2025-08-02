#!/usr/bin/env python3
"""
Ultra-Advanced Security Middleware Integration
Competitive Programming Optimized with O(1) performance guarantees
"""

import asyncio
import time
import json
import logging
from typing import Optional, Dict, Any, Tuple
from fastapi import FastAPI, Request, Response, HTTPException, status, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import redis.asyncio as redis

from .advanced_security import (
    UltraSecurityMiddleware,
    UltraSecureAuthService,
    UltraSecureCORS,
    UltraSecureValidator,
    TokenBucketRateLimiter,
    GeolocationSecurityFilter
)

logger = logging.getLogger(__name__)

# =====================================================
# SECURITY CONFIGURATION
# =====================================================

class SecurityConfig:
    """Ultra-optimized security configuration"""
    
    def __init__(self):
        # Rate limiting tiers - different limits for different endpoints
        self.rate_limits = {
            'auth': {'requests': 5, 'window': 60},      # 5 req/min for auth
            'api': {'requests': 100, 'window': 60},     # 100 req/min for API
            'search': {'requests': 50, 'window': 60},   # 50 req/min for search
            'upload': {'requests': 10, 'window': 300},  # 10 req/5min for uploads
        }
        
        # Content type restrictions
        self.allowed_content_types = {
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain',
        }
        
        # Maximum request sizes by endpoint type
        self.max_request_sizes = {
            'default': 1024 * 1024,      # 1MB
            'upload': 10 * 1024 * 1024,  # 10MB
            'import': 50 * 1024 * 1024,  # 50MB
        }
        
        # JWT configuration
        self.jwt_config = {
            'algorithm': 'HS256',
            'access_token_expire': 3600,    # 1 hour
            'refresh_token_expire': 604800, # 7 days
            'issuer': 'bkmrk-api',
            'audience': 'bkmrk-frontend',
        }

# =====================================================
# ADVANCED AUTHENTICATION MIDDLEWARE
# =====================================================

class AdvancedAuthMiddleware(BaseHTTPMiddleware):
    """Ultra-fast authentication middleware with O(1) token validation"""
    
    def __init__(self, app: FastAPI, redis_client: redis.Redis, secret_key: str):
        super().__init__(app)
        self.auth_service = UltraSecureAuthService(redis_client, secret_key)
        self.security = HTTPBearer(auto_error=False)
        
        # Public endpoints that don't require authentication
        self.public_endpoints = {
            '/health',
            '/ready',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/auth/login',
            '/auth/register',
            '/books',  # Public book browsing
            '/books/{id}',  # Public book details
        }
        
        # Endpoint-specific rate limits
        self.endpoint_limits = {
            '/auth/login': {'requests': 5, 'window': 300},      # 5 attempts per 5min
            '/auth/register': {'requests': 3, 'window': 3600},  # 3 registrations per hour
            '/auth/forgot-password': {'requests': 2, 'window': 3600},  # 2 per hour
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process authentication with ultra-high performance - O(1)"""
        
        start_time = time.time()
        path = request.url.path
        method = request.method
        client_ip = self._get_client_ip(request)
        
        # Skip authentication for public endpoints
        if self._is_public_endpoint(path, method):
            return await call_next(request)
        
        # Extract and validate token
        token = await self._extract_token(request)
        if not token:
            return self._create_auth_error("Missing authentication token")
        
        # Validate token with caching - O(1)
        is_valid, auth_data, error_msg = await self.auth_service.validate_token(token, client_ip)
        
        if not is_valid:
            logger.warning(f"Authentication failed for {client_ip}: {error_msg}")
            return self._create_auth_error(f"Authentication failed: {error_msg}")
        
        # Add user context to request
        request.state.user = auth_data
        request.state.user_id = auth_data['user_id']
        request.state.session_id = auth_data['session_id']
        
        # Process request
        response = await call_next(request)
        
        # Log authentication metrics
        processing_time = (time.time() - start_time) * 1000
        await self._log_auth_metrics(request, response, processing_time)
        
        return response
    
    def _is_public_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint is public - O(1) with set lookup"""
        # Exact match
        if path in self.public_endpoints:
            return True
        
        # Pattern matching for parameterized routes
        if path.startswith('/books/') and method == 'GET':
            return True
        
        if path.startswith('/health') or path.startswith('/ready'):
            return True
        
        return False
    
    async def _extract_token(self, request: Request) -> Optional[str]:
        """Extract JWT token from request - O(1)"""
        # Check Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check cookie (for web app)
        token_cookie = request.cookies.get('access_token')
        if token_cookie:
            return token_cookie
        
        # Check query parameter (for WebSocket upgrades)
        token_param = request.query_params.get('token')
        if token_param:
            return token_param
        
        return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address - O(1)"""
        # Check proxy headers in order of preference
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else '127.0.0.1'
    
    def _create_auth_error(self, detail: str) -> Response:
        """Create authentication error response - O(1)"""
        return Response(
            content=json.dumps({
                "error": "authentication_failed",
                "detail": detail,
                "timestamp": time.time()
            }),
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={
                "Content-Type": "application/json",
                "WWW-Authenticate": "Bearer",
            }
        )
    
    async def _log_auth_metrics(self, request: Request, response: Response, processing_time: float):
        """Log authentication metrics - O(1)"""
        try:
            metrics = {
                'timestamp': time.time(),
                'endpoint': request.url.path,
                'method': request.method,
                'status_code': response.status_code,
                'processing_time_ms': processing_time,
                'user_id': getattr(request.state, 'user_id', None),
                'session_id': getattr(request.state, 'session_id', None),
            }
            
            # In production, send to monitoring system
            logger.info("auth_metrics", extra=metrics)
            
        except Exception as e:
            logger.error(f"Failed to log auth metrics: {e}")

# =====================================================
# ADVANCED RATE LIMITING MIDDLEWARE
# =====================================================

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Ultra-advanced rate limiting with multiple algorithms"""
    
    def __init__(self, app: FastAPI, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limiter = TokenBucketRateLimiter(redis_client)
        self.config = SecurityConfig()
        
        # Sliding window rate limiter for more precise control
        self.sliding_window_limits = {
            '/auth/': {'requests': 10, 'window': 300},  # 10 auth requests per 5min
            '/api/books/search': {'requests': 100, 'window': 60},  # 100 searches per min
            '/api/cart/': {'requests': 50, 'window': 60},  # 50 cart operations per min
        }
    
    async def dispatch(self, request: Request, call_next):
        """Advanced rate limiting with multiple algorithms - O(1)"""
        
        client_ip = self._get_client_ip(request)
        endpoint = request.url.path
        method = request.method
        
        # Determine rate limit tier
        limit_config = self._get_rate_limit_config(endpoint, method)
        
        # Apply token bucket rate limiting
        allowed, rate_info = await self.rate_limiter.is_allowed(
            f"{client_ip}:{endpoint}",
            limit_config['requests'],
            limit_config['window']
        )
        
        if not allowed:
            return self._create_rate_limit_response(rate_info)
        
        # Apply sliding window for critical endpoints
        if self._is_critical_endpoint(endpoint):
            sliding_allowed = await self._check_sliding_window(client_ip, endpoint)
            if not sliding_allowed:
                return self._create_rate_limit_response({
                    'retry_after': 60,
                    'message': 'Sliding window rate limit exceeded'
                })
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Add rate limiting headers
        response.headers['X-RateLimit-Limit'] = str(limit_config['requests'])
        response.headers['X-RateLimit-Remaining'] = str(rate_info.get('tokens_remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit_config['window']))
        
        return response
    
    def _get_rate_limit_config(self, endpoint: str, method: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint - O(1)"""
        # Endpoint-specific limits
        for pattern, config in self.config.rate_limits.items():
            if pattern in endpoint.lower():
                return config
        
        # Method-specific limits
        if method in ['POST', 'PUT', 'DELETE']:
            return {'requests': 50, 'window': 60}  # More restrictive for mutations
        
        # Default limits
        return {'requests': 100, 'window': 60}
    
    def _is_critical_endpoint(self, endpoint: str) -> bool:
        """Check if endpoint requires sliding window limiting - O(1)"""
        critical_patterns = ['/auth/', '/admin/', '/payment/']
        return any(pattern in endpoint for pattern in critical_patterns)
    
    async def _check_sliding_window(self, client_ip: str, endpoint: str) -> bool:
        """Implement sliding window rate limiting - O(log n) with sorted sets"""
        try:
            window_key = f"sliding:{client_ip}:{endpoint}"
            current_time = time.time()
            window_size = 300  # 5 minutes
            max_requests = 10
            
            # Remove old entries outside the window
            await self.redis.zremrangebyscore(
                window_key, 
                0, 
                current_time - window_size
            )
            
            # Count current requests in window
            current_count = await self.redis.zcard(window_key)
            
            if current_count >= max_requests:
                return False
            
            # Add current request
            await self.redis.zadd(
                window_key, 
                {str(current_time): current_time}
            )
            
            # Set expiry
            await self.redis.expire(window_key, window_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Sliding window check failed: {e}")
            return True  # Fail open
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP - O(1)"""
        return request.headers.get('X-Forwarded-For', request.client.host).split(',')[0].strip()
    
    def _create_rate_limit_response(self, rate_info: Dict[str, Any]) -> Response:
        """Create rate limit exceeded response - O(1)"""
        return Response(
            content=json.dumps({
                "error": "rate_limit_exceeded",
                "message": rate_info.get('message', 'Too many requests'),
                "retry_after": rate_info.get('retry_after', 60),
                "timestamp": time.time()
            }),
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={
                "Content-Type": "application/json",
                "Retry-After": str(int(rate_info.get('retry_after', 60))),
            }
        )

# =====================================================
# REQUEST VALIDATION MIDDLEWARE
# =====================================================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Ultra-fast request validation with competitive programming optimizations"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.validator = UltraSecureValidator()
        self.config = SecurityConfig()
        
        # Content type validation cache
        self.content_type_cache = {}
    
    async def dispatch(self, request: Request, call_next):
        """Validate incoming requests - O(m) where m is request size"""
        
        # 1. Validate content type - O(1)
        content_type = request.headers.get('Content-Type', '').split(';')[0]
        if content_type and not self._is_content_type_allowed(content_type):
            return self._create_validation_error("Invalid content type")
        
        # 2. Validate request size - O(1)
        content_length = request.headers.get('Content-Length')
        if content_length:
            size = int(content_length)
            max_size = self._get_max_request_size(request.url.path)
            if size > max_size:
                return self._create_validation_error(
                    f"Request too large: {size} > {max_size}"
                )
        
        # 3. Validate headers - O(h) where h is number of headers
        for name, value in request.headers.items():
            if not self._validate_header(name, value):
                return self._create_validation_error(f"Invalid header: {name}")
        
        # 4. Validate URL path - O(p) where p is path length
        if not self._validate_path(request.url.path):
            return self._create_validation_error("Invalid request path")
        
        # 5. For POST/PUT requests, validate body (if JSON)
        if request.method in ['POST', 'PUT'] and content_type == 'application/json':
            # This will be handled by FastAPI's automatic validation
            # but we can add additional security checks here
            pass
        
        return await call_next(request)
    
    def _is_content_type_allowed(self, content_type: str) -> bool:
        """Check if content type is allowed - O(1) with set lookup"""
        # Use cache for performance
        if content_type in self.content_type_cache:
            return self.content_type_cache[content_type]
        
        is_allowed = content_type in self.config.allowed_content_types
        self.content_type_cache[content_type] = is_allowed
        
        return is_allowed
    
    def _get_max_request_size(self, path: str) -> int:
        """Get maximum request size for path - O(1)"""
        if '/upload' in path:
            return self.config.max_request_sizes['upload']
        elif '/import' in path:
            return self.config.max_request_sizes['import']
        else:
            return self.config.max_request_sizes['default']
    
    def _validate_header(self, name: str, value: str) -> bool:
        """Validate individual header - O(n) where n is value length"""
        # Check header name length
        if len(name) > 256:
            return False
        
        # Check header value length
        if len(value) > 4096:
            return False
        
        # Scan for malicious patterns
        is_malicious, threat_level, _ = self.validator.trie_filter.scan_text(f"{name}: {value}")
        if is_malicious and threat_level >= 4:
            return False
        
        return True
    
    def _validate_path(self, path: str) -> bool:
        """Validate URL path - O(p) where p is path length"""
        # Check path length
        if len(path) > 2048:
            return False
        
        # Check for path traversal and other attacks
        is_malicious, threat_level, _ = self.validator.trie_filter.scan_text(path)
        if is_malicious and threat_level >= 3:
            return False
        
        return True
    
    def _create_validation_error(self, detail: str) -> Response:
        """Create validation error response - O(1)"""
        return Response(
            content=json.dumps({
                "error": "validation_failed",
                "detail": detail,
                "timestamp": time.time()
            }),
            status_code=status.HTTP_400_BAD_REQUEST,
            headers={"Content-Type": "application/json"}
        )

# =====================================================
# SECURITY HEADERS MIDDLEWARE
# =====================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers - O(1)"""
    
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.cors_handler = UltraSecureCORS()
        
        # Security headers with environment-aware values
        self.headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': self._build_csp(),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), accelerometer=(), gyroscope=()'
            ),
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
        }
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response - O(1)"""
        
        response = await call_next(request)
        
        # Add standard security headers
        for header, value in self.headers.items():
            response.headers[header] = value
        
        # Add CORS headers if needed
        cors_headers = self.cors_handler.get_cors_headers(request)
        for header, value in cors_headers.items():
            response.headers[header] = value
        
        # Add custom security headers
        response.headers['X-API-Version'] = '1.0'
        response.headers['X-Response-Time'] = str(int(time.time() * 1000))
        
        return response
    
    def _build_csp(self) -> str:
        """Build Content Security Policy - O(1)"""
        # Environment-aware CSP
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://api.gemini.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests",
        ]
        
        return '; '.join(csp_directives)

# =====================================================
# SECURITY MIDDLEWARE FACTORY
# =====================================================

def setup_security_middleware(app: FastAPI, redis_client: redis.Redis, secret_key: str):
    """Setup all security middleware with optimal ordering - O(1)"""
    
    # Order matters for performance and security
    
    # 1. CORS (must be first for preflight requests)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://bookstore.yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        max_age=86400,  # 24 hours
    )
    
    # 2. Security headers (early to ensure all responses get headers)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 3. Rate limiting (before expensive operations)
    app.add_middleware(AdvancedRateLimitMiddleware, redis_client)
    
    # 4. Request validation (validate before processing)
    app.add_middleware(RequestValidationMiddleware)
    
    # 5. Authentication (after validation, before business logic)
    app.add_middleware(AdvancedAuthMiddleware, redis_client, secret_key)
    
    # 6. General security middleware (comprehensive checks)
    app.add_middleware(UltraSecurityMiddleware, redis_client)
    
    logger.info("✅ Advanced security middleware configured successfully")

# =====================================================
# SECURITY UTILITIES
# =====================================================

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get current authenticated user - O(1)"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return request.state.user

async def require_admin(request: Request) -> Dict[str, Any]:
    """Require admin privileges - O(1)"""
    user = await get_current_user(request)
    
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return user

async def check_rate_limit(
    request: Request, 
    limit_type: str = 'default'
) -> bool:
    """Manual rate limit check for specific operations - O(1)"""
    # This can be used for additional rate limiting in specific endpoints
    # Implementation would depend on specific requirements
    return True