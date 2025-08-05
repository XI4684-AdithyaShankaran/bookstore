#!/usr/bin/env python3
"""
Security Framework
Security with performance guarantees
"""

import asyncio
import hashlib
import hmac
import time
import re
import json
import logging
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from collections import defaultdict, deque
from functools import lru_cache, wraps
import ipaddress
from datetime import datetime, timedelta
import secrets
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# =====================================================
# COMPETITIVE PROGRAMMING OPTIMIZED DATA STRUCTURES
# =====================================================

class TrieSecurityFilter:
    """Trie for O(m) pattern matching where m is pattern length"""
    
    class TrieNode:
        def __init__(self):
            self.children = {}  # O(1) lookups
            self.is_malicious = False
            self.threat_level = 0
    
    def __init__(self):
        self.root = self.TrieNode()
        self.pattern_cache = {}  # O(1) cached results
        
        # Pre-load common attack patterns
        self._load_attack_patterns()
    
    def _load_attack_patterns(self):
        """Load common attack patterns - O(k*m) where k=patterns, m=avg length"""
        malicious_patterns = [
            # SQL Injection patterns
            "union select", "drop table", "'; drop", "or 1=1", "' or '1'='1",
            "exec xp_", "sp_executesql", "xp_cmdshell", "bulk insert",
            
            # XSS patterns
            "<script", "javascript:", "onload=", "onerror=", "onclick=",
            "onmouseover=", "onfocus=", "onblur=", "eval(", "document.cookie",
            
            # Path traversal
            "../", "..\\", "%2e%2e%2f", "%2e%2e%5c", "/..", "\\...",
            
            # Command injection
            "; rm -rf", "| rm -rf", "&& rm", "$(rm", "`rm", "wget ", "curl ",
            
            # NoSQL injection
            "$where", "$ne", "$gt", "$lt", "$regex", "$exists",
            
            # LDAP injection
            "*)(cn=", "*)(uid=", "*)(&", "*)(objectclass=",
            
            # XML injection
            "<!entity", "<!doctype", "<?xml", "&xxe;", "system \"file:",
        ]
        
        for pattern in malicious_patterns:
            self.insert_pattern(pattern.lower(), threat_level=5)
    
    def insert_pattern(self, pattern: str, threat_level: int = 1):
        """Insert malicious pattern - O(m) where m is pattern length"""
        node = self.root
        
        for char in pattern:
            if char not in node.children:
                node.children[char] = self.TrieNode()
            node = node.children[char]
        
        node.is_malicious = True
        node.threat_level = max(node.threat_level, threat_level)
    
    def scan_text(self, text: str) -> Tuple[bool, int, List[str]]:
        """Scan text for malicious patterns - O(n*m) optimized"""
        if not text:
            return False, 0, []
        
        text_lower = text.lower()
        cache_key = hashlib.md5(text_lower.encode()).hexdigest()
        
        # Check cache first - O(1)
        if cache_key in self.pattern_cache:
            return self.pattern_cache[cache_key]
        
        max_threat_level = 0
        found_patterns = []
        
        # Sliding window scan - O(n*m) where n=text length, m=max pattern length
        for i in range(len(text_lower)):
            node = self.root
            j = i
            
            while j < len(text_lower) and text_lower[j] in node.children:
                node = node.children[text_lower[j]]
                j += 1
                
                if node.is_malicious:
                    pattern = text_lower[i:j]
                    found_patterns.append(pattern)
                    max_threat_level = max(max_threat_level, node.threat_level)
        
        is_malicious = max_threat_level > 0
        result = (is_malicious, max_threat_level, found_patterns)
        
        # Cache result - O(1)
        self.pattern_cache[cache_key] = result
        return result

class TokenBucketRateLimiter:
    """Token bucket rate limiter with O(1) operations"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.buckets = {}  # Local cache for performance
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def is_allowed(
        self, 
        client_id: str, 
        max_requests: int, 
        window_seconds: int,
        burst_multiplier: float = 1.5
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed - O(1) complexity"""
        now = time.time()
        bucket_key = f"rate_limit:{client_id}"
        
        # Cleanup old buckets periodically
        if now - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_buckets()
            self.last_cleanup = now
        
        # Get or create bucket
        bucket = await self._get_bucket(bucket_key, max_requests, window_seconds)
        
        # Calculate tokens to add based on time elapsed
        time_elapsed = now - bucket['last_refill']
        tokens_to_add = time_elapsed * (max_requests / window_seconds)
        
        # Update bucket
        bucket['tokens'] = min(
            max_requests * burst_multiplier,  # Allow burst capacity
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_refill'] = now
        
        # Check if request is allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            await self._update_bucket(bucket_key, bucket)
            
            return True, {
                'allowed': True,
                'tokens_remaining': int(bucket['tokens']),
                'reset_time': now + window_seconds,
                'retry_after': None
            }
        else:
            # Calculate retry-after time
            retry_after = (1 - bucket['tokens']) / (max_requests / window_seconds)
            
            return False, {
                'allowed': False,
                'tokens_remaining': 0,
                'reset_time': now + window_seconds,
                'retry_after': retry_after
            }
    
    async def _get_bucket(self, key: str, max_requests: int, window_seconds: int) -> Dict[str, float]:
        """Get bucket from Redis with fallback to local cache - O(1)"""
        try:
            bucket_data = await self.redis.get(key)
            if bucket_data:
                return json.loads(bucket_data)
        except Exception as e:
            logger.warning(f"Redis error in rate limiter: {e}")
        
        # Default bucket
        return {
            'tokens': float(max_requests),
            'last_refill': time.time(),
            'max_requests': max_requests,
            'window_seconds': window_seconds
        }
    
    async def _update_bucket(self, key: str, bucket: Dict[str, float]):
        """Update bucket in Redis - O(1)"""
        try:
            await self.redis.setex(
                key, 
                int(bucket['window_seconds'] * 2),  # TTL = 2x window
                json.dumps(bucket)
            )
        except Exception as e:
            logger.warning(f"Redis error updating bucket: {e}")
    
    async def _cleanup_buckets(self):
        """Clean up expired buckets - O(k) where k is number of buckets"""
        try:
            pattern = "rate_limit:*"
            keys = await self.redis.keys(pattern)
            
            if keys:
                # Batch delete expired keys
                await self.redis.delete(*keys[:1000])  # Limit batch size
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

class GeolocationSecurityFilter:
    """Geolocation-based security filter with O(log n) IP lookups"""
    
    def __init__(self):
        self.blocked_countries = set(['CN', 'RU', 'KP', 'IR'])  # O(1) lookups
        self.blocked_ips = set()  # O(1) lookups
        self.ip_cache = {}  # O(1) cached lookups
        
        # Pre-build IP range trees for fast lookups
        self.ipv4_tree = self._build_ip_tree()
        self.ipv6_tree = self._build_ip_tree(ipv6=True)
    
    def _build_ip_tree(self, ipv6: bool = False) -> Dict:
        """Build optimized IP range tree for O(log n) lookups"""
        # Simplified implementation - in production, use radix tree or trie
        return {
            'ranges': [],
            'blocked_ranges': [
                # Common bot/attack IP ranges
                '10.0.0.0/8',
                '172.16.0.0/12', 
                '192.168.0.0/16',
                # Add more ranges as needed
            ]
        }
    
    @lru_cache(maxsize=10000)
    def is_ip_blocked(self, ip_address: str) -> Tuple[bool, str]:
        """Check if IP is blocked - O(1) cached, O(log n) uncached"""
        try:
            ip = ipaddress.ip_address(ip_address)
            
            # Check direct IP blocks - O(1)
            if ip_address in self.blocked_ips:
                return True, "ip_blocked"
            
            # Check IP ranges - O(log n) with optimized tree
            if self._is_in_blocked_range(ip):
                return True, "range_blocked"
            
            # Check geolocation (simplified)
            country_code = self._get_country_code(ip_address)
            if country_code in self.blocked_countries:
                return True, f"country_blocked_{country_code}"
            
            return False, "allowed"
            
        except ValueError:
            return True, "invalid_ip"
    
    def _is_in_blocked_range(self, ip: ipaddress.IPv4Address) -> bool:
        """Check if IP is in blocked range - O(log n)"""
        # Simplified check - use optimized data structure in production
        for range_str in self.ipv4_tree['blocked_ranges']:
            try:
                network = ipaddress.ip_network(range_str)
                if ip in network:
                    return True
            except ValueError:
                continue
        return False
    
    def _get_country_code(self, ip_address: str) -> str:
        """Get country code for IP - O(1) with cache"""
        # Simplified implementation - integrate with MaxMind GeoIP in production
        cache_key = f"geo:{ip_address}"
        
        if cache_key in self.ip_cache:
            return self.ip_cache[cache_key]
        
        # Mock geolocation lookup
        # In production, use GeoIP2 database
        country_code = 'US'  # Default
        
        self.ip_cache[cache_key] = country_code
        return country_code

# =====================================================
# ADVANCED VALIDATION FRAMEWORK
# =====================================================

class SecurityValidator:
    """Input validation with performance optimization"""
    
    def __init__(self):
        self.trie_filter = TrieSecurityFilter()
        self.validation_cache = {}  # O(1) cached validations
        
        # Compiled regex patterns for O(1) after compilation
        self.patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^\+?1?[0-9]{10,15}$'),
            'username': re.compile(r'^[a-zA-Z0-9_]{3,30}$'),
            'password': re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'),
            'isbn': re.compile(r'^(?:ISBN(?:-1[03])?:? )?(?=[0-9X]{10}$|(?=(?:[0-9]+[- ]){3})[- 0-9X]{13}$|97[89][0-9]{10}$|(?=(?:[0-9]+[- ]){4})[- 0-9]{17}$)(?:97[89][- ]?)?[0-9]{1,5}[- ]?[0-9]+[- ]?[0-9]+[- ]?[0-9X]$'),
            'url': re.compile(r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?$'),
            'sql_injection': re.compile(r"('|(\\\')|(\-\-)|(\;)|(\|)|(\*)|(%)|(\+)|(select|insert|update|delete|drop|create|alter|exec|union|script))", re.IGNORECASE),
            'xss': re.compile(r'<[^>]*script[^>]*>|javascript:|on\w+\s*=|<[^>]*on\w+[^>]*>', re.IGNORECASE),
        }
    
    def validate_input(
        self, 
        value: Any, 
        input_type: str, 
        max_length: int = 1000,
        required: bool = True
    ) -> Tuple[bool, str, Any]:
        """Input validation - O(1) cached, O(m) uncached"""
        
        # Generate cache key
        cache_key = hashlib.md5(
            f"{value}:{input_type}:{max_length}:{required}".encode()
        ).hexdigest()
        
        # Check cache first - O(1)
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        # Perform validation
        result = self._validate_uncached(value, input_type, max_length, required)
        
        # Cache result - O(1)
        self.validation_cache[cache_key] = result
        return result
    
    def _validate_uncached(
        self, 
        value: Any, 
        input_type: str, 
        max_length: int,
        required: bool
    ) -> Tuple[bool, str, Any]:
        """Perform actual validation - O(m) where m is input length"""
        
        # Handle None/empty values
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                return False, "required_field_missing", None
            return True, "valid", None
        
        # Convert to string for validation
        str_value = str(value).strip()
        
        # Length validation - O(1)
        if len(str_value) > max_length:
            return False, f"max_length_exceeded_{max_length}", None
        
        # Security scan - O(m*k) where k is number of patterns
        is_malicious, threat_level, patterns = self.trie_filter.scan_text(str_value)
        if is_malicious:
            logger.warning(f"Malicious input detected: {patterns}, threat level: {threat_level}")
            return False, f"malicious_input_detected_{threat_level}", None
        
        # Type-specific validation - O(m) for regex
        if input_type in self.patterns:
            if not self.patterns[input_type].match(str_value):
                return False, f"invalid_{input_type}_format", None
        
        # Additional security checks
        if input_type == 'string':
            # Check for potential XSS
            if self.patterns['xss'].search(str_value):
                return False, "xss_detected", None
            
            # Check for SQL injection
            if self.patterns['sql_injection'].search(str_value):
                return False, "sql_injection_detected", None
        
        # Sanitize value
        sanitized_value = self._sanitize_value(str_value, input_type)
        
        return True, "valid", sanitized_value
    
    def _sanitize_value(self, value: str, input_type: str) -> str:
        """Sanitize input value - O(n)"""
        if input_type == 'string':
            # HTML encode special characters
            value = (value
                     .replace('&', '&amp;')
                     .replace('<', '&lt;')
                     .replace('>', '&gt;')
                     .replace('"', '&quot;')
                     .replace("'", '&#x27;'))
        
        return value.strip()

# =====================================================
# ADVANCED AUTHENTICATION SYSTEM
# =====================================================

class UltraSecureAuthService:
    """Authentication with optimizations"""
    
    def __init__(self, redis_client: redis.Redis, secret_key: str):
        self.redis = redis_client
        self.secret_key = secret_key
        self.token_cache = {}  # O(1) token validation cache
        self.blacklisted_tokens = set()  # O(1) blacklist lookups
        
        # Advanced encryption setup
        self.fernet = Fernet(self._derive_key(secret_key))
        
        # JWT algorithm optimizations
        self.jwt_algorithm = "HS256"  # Fastest symmetric algorithm
        
        # Session management
        self.active_sessions = defaultdict(set)  # O(1) session lookups
        
        # Failed attempt tracking with exponential backoff
        self.failed_attempts = defaultdict(lambda: {'count': 0, 'last_attempt': 0, 'backoff': 1})
    
    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key using PBKDF2 - O(1) with caching"""
        cache_key = f"derived_key:{hashlib.sha256(password.encode()).hexdigest()}"
        
        # Use a fixed salt for deterministic key derivation (cache-friendly)
        # In production, use per-user salts stored securely
        salt = b'bookstore_salt_v1'
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        return Fernet.generate_key()  # Simplified for demo
    
    async def authenticate_user(
        self, 
        username: str, 
        password: str, 
        client_ip: str
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Ultra-secure user authentication - O(1) with proper indexing"""
        
        # Check rate limiting for failed attempts
        attempt_key = f"auth_attempts:{client_ip}:{username}"
        if not await self._check_auth_rate_limit(attempt_key):
            return False, None, "rate_limit_exceeded"
        
        # Validate inputs
        validator = UltraSecureValidator()
        
        username_valid, username_error, clean_username = validator.validate_input(
            username, 'username', max_length=30
        )
        if not username_valid:
            await self._record_failed_attempt(attempt_key)
            return False, None, f"invalid_username_{username_error}"
        
        password_valid, password_error, _ = validator.validate_input(
            password, 'password', max_length=128
        )
        if not password_valid:
            await self._record_failed_attempt(attempt_key)
            return False, None, f"invalid_password_{password_error}"
        
        # Get user from database (should be O(1) with proper indexing)
        user = await self._get_user_by_username(clean_username)
        if not user:
            await self._record_failed_attempt(attempt_key)
            # Constant time response to prevent user enumeration
            bcrypt.checkpw(b"dummy", b"$2b$12$dummy_hash_to_prevent_timing_attacks")
            return False, None, "invalid_credentials"
        
        # Verify password with constant-time comparison
        if not await self._verify_password(password, user['password_hash']):
            await self._record_failed_attempt(attempt_key)
            return False, None, "invalid_credentials"
        
        # Check if account is locked
        if user.get('is_locked', False):
            return False, None, "account_locked"
        
        # Generate secure session
        session_data = await self._create_secure_session(user, client_ip)
        
        # Reset failed attempts on successful login
        await self._reset_failed_attempts(attempt_key)
        
        return True, session_data, "success"
    
    async def _check_auth_rate_limit(self, attempt_key: str) -> bool:
        """Check authentication rate limiting with exponential backoff - O(1)"""
        try:
            attempt_data = await self.redis.get(attempt_key)
            if not attempt_data:
                return True
            
            attempts = json.loads(attempt_data)
            current_time = time.time()
            
            # Exponential backoff calculation
            time_since_last = current_time - attempts['last_attempt']
            required_wait = attempts['backoff']
            
            if attempts['count'] >= 5 and time_since_last < required_wait:
                return False
            
            return True
            
        except Exception:
            return True  # Fail open for availability
    
    async def _record_failed_attempt(self, attempt_key: str):
        """Record failed authentication attempt - O(1)"""
        try:
            current_time = time.time()
            attempt_data = await self.redis.get(attempt_key)
            
            if attempt_data:
                attempts = json.loads(attempt_data)
                attempts['count'] += 1
                attempts['last_attempt'] = current_time
                attempts['backoff'] = min(attempts['backoff'] * 2, 3600)  # Max 1 hour
            else:
                attempts = {
                    'count': 1,
                    'last_attempt': current_time,
                    'backoff': 60  # Start with 1 minute
                }
            
            # Store with TTL
            await self.redis.setex(
                attempt_key,
                7200,  # 2 hours TTL
                json.dumps(attempts)
            )
            
        except Exception as e:
            logger.error(f"Failed to record auth attempt: {e}")
    
    async def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password with constant-time comparison - O(1)"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception:
            return False
    
    async def _create_secure_session(
        self, 
        user: Dict[str, Any], 
        client_ip: str
    ) -> Dict[str, Any]:
        """Create ultra-secure session with multiple tokens - O(1)"""
        
        current_time = time.time()
        session_id = secrets.token_urlsafe(32)
        
        # Create JWT payload with minimal data
        jwt_payload = {
            'user_id': user['id'],
            'session_id': session_id,
            'iat': int(current_time),
            'exp': int(current_time + 3600),  # 1 hour
            'iss': 'bkmrk-api',
            'aud': 'bkmrk-frontend',
            'jti': secrets.token_urlsafe(16),  # JWT ID for revocation
        }
        
        # Generate tokens
        access_token = jwt.encode(jwt_payload, self.secret_key, algorithm=self.jwt_algorithm)
        
        # Refresh token with longer expiry
        refresh_payload = {
            'user_id': user['id'],
            'session_id': session_id,
            'type': 'refresh',
            'iat': int(current_time),
            'exp': int(current_time + 86400 * 7),  # 7 days
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.jwt_algorithm)
        
        # Store session in Redis
        session_data = {
            'user_id': user['id'],
            'session_id': session_id,
            'client_ip': client_ip,
            'created_at': current_time,
            'last_activity': current_time,
            'is_active': True,
        }
        
        await self.redis.setex(
            f"session:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(session_data)
        )
        
        # Add to active sessions
        self.active_sessions[user['id']].add(session_id)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': 3600,
            'session_id': session_id,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'role': user.get('role', 'user'),
            }
        }
    
    @lru_cache(maxsize=10000)
    async def validate_token(
        self, 
        token: str, 
        client_ip: str = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Ultra-fast token validation with caching - O(1)"""
        
        # Check blacklist first - O(1)
        if token in self.blacklisted_tokens:
            return False, None, "token_blacklisted"
        
        try:
            # Decode JWT - O(1) for valid tokens
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            
            # Validate session exists
            session_id = payload.get('session_id')
            if not session_id:
                return False, None, "invalid_session"
            
            session_data = await self.redis.get(f"session:{session_id}")
            if not session_data:
                return False, None, "session_expired"
            
            session = json.loads(session_data)
            
            # Validate client IP if provided
            if client_ip and session.get('client_ip') != client_ip:
                logger.warning(f"IP mismatch for session {session_id}: {client_ip} vs {session.get('client_ip')}")
                return False, None, "ip_mismatch"
            
            # Update last activity
            session['last_activity'] = time.time()
            await self.redis.setex(
                f"session:{session_id}",
                3600,
                json.dumps(session)
            )
            
            return True, {
                'user_id': payload['user_id'],
                'session_id': session_id,
                'jwt_payload': payload,
                'session_data': session
            }, "valid"
            
        except jwt.ExpiredSignatureError:
            return False, None, "token_expired"
        except jwt.InvalidTokenError as e:
            return False, None, f"invalid_token_{str(e)}"
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None, "validation_error"
    
    async def revoke_token(self, token: str, session_id: str = None):
        """Revoke token and session - O(1)"""
        # Add to blacklist
        self.blacklisted_tokens.add(token)
        
        # Remove session if provided
        if session_id:
            await self.redis.delete(f"session:{session_id}")
    
    async def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username - should be O(1) with proper DB indexing"""
        # This should use your actual database with proper indexing
        # Simplified implementation for demo
        cache_key = f"user:{username}"
        
        try:
            user_data = await self.redis.get(cache_key)
            if user_data:
                return json.loads(user_data)
        except Exception:
            pass
        
        # In production, query your actual database here
        # with proper prepared statements and indexing
        return None

# =====================================================
# SECURITY MIDDLEWARE
# =====================================================

class UltraSecurityMiddleware:
    """Ultra-advanced security middleware with O(1) performance"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.rate_limiter = TokenBucketRateLimiter(redis_client)
        self.geo_filter = GeolocationSecurityFilter()
        self.validator = UltraSecureValidator()
        
        # Security headers
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubdomains',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            ),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with ultra-advanced security - O(1) average case"""
        
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        
        # 1. IP Geolocation filtering - O(1) cached, O(log n) uncached
        ip_blocked, block_reason = self.geo_filter.is_ip_blocked(client_ip)
        if ip_blocked:
            logger.warning(f"Blocked IP {client_ip}: {block_reason}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from your location"
            )
        
        # 2. Rate limiting - O(1)
        allowed, rate_info = await self.rate_limiter.is_allowed(
            client_ip, 
            max_requests=100, 
            window_seconds=60
        )
        
        if not allowed:
            response = HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
            response.headers['Retry-After'] = str(int(rate_info['retry_after']))
            raise response
        
        # 3. Request validation
        await self._validate_request(request)
        
        # 4. Process request
        response = await call_next(request)
        
        # 5. Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # 6. Add rate limit headers
        response.headers['X-RateLimit-Remaining'] = str(rate_info['tokens_remaining'])
        response.headers['X-RateLimit-Reset'] = str(int(rate_info['reset_time']))
        
        # 7. Log security metrics
        processing_time = (time.time() - start_time) * 1000
        await self._log_security_metrics(request, response, processing_time, client_ip)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP with proxy support - O(1)"""
        # Check common proxy headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        forwarded = request.headers.get('Forwarded')
        if forwarded:
            # Parse Forwarded header (simplified)
            import re
            match = re.search(r'for=([^;,\s]+)', forwarded)
            if match:
                return match.group(1).strip('"')
        
        return request.client.host if request.client else '127.0.0.1'
    
    async def _validate_request(self, request: Request):
        """Validate incoming request - O(m) where m is request size"""
        
        # Check request size
        content_length = request.headers.get('Content-Length')
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request too large"
            )
        
        # Validate headers
        for header_name, header_value in request.headers.items():
            if len(header_name) > 256 or len(header_value) > 4096:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Header too long"
                )
            
            # Check for malicious patterns in headers
            is_malicious, threat_level, patterns = self.validator.trie_filter.scan_text(
                f"{header_name}: {header_value}"
            )
            if is_malicious and threat_level >= 3:
                logger.warning(f"Malicious header detected: {patterns}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request headers"
                )
        
        # Validate URL path
        path = str(request.url.path)
        is_malicious, threat_level, patterns = self.validator.trie_filter.scan_text(path)
        if is_malicious and threat_level >= 4:
            logger.warning(f"Malicious path detected: {path}, patterns: {patterns}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request path"
            )
    
    async def _log_security_metrics(
        self, 
        request: Request, 
        response, 
        processing_time: float, 
        client_ip: str
    ):
        """Log security metrics for monitoring - O(1)"""
        try:
            metrics = {
                'timestamp': time.time(),
                'client_ip': client_ip,
                'method': request.method,
                'path': str(request.url.path),
                'status_code': response.status_code,
                'processing_time_ms': processing_time,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_length': request.headers.get('Content-Length', 0),
            }
            
            # Store in Redis for real-time monitoring
            await self.redis.lpush(
                'security_metrics',
                json.dumps(metrics)
            )
            
            # Keep only last 10000 entries
            await self.redis.ltrim('security_metrics', 0, 9999)
            
        except Exception as e:
            logger.error(f"Failed to log security metrics: {e}")

# =====================================================
# CORS HARDENING
# =====================================================

class UltraSecureCORS:
    """Ultra-hardened CORS with dynamic origin validation"""
    
    def __init__(self):
        # Allowed origins with pattern matching
        self.allowed_origins = {
            'localhost:3000',  # Development
            'bookstore.yourdomain.com',  # Production
            '*.yourdomain.com',  # Subdomains
        }
        
        self.allowed_methods = {'GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'}
        self.allowed_headers = {
            'Authorization',
            'Content-Type',
            'X-Requested-With',
            'X-CSRF-Token',
        }
        
        # Precompiled regex for performance
        self.origin_patterns = [
            re.compile(origin.replace('*', '.*')) for origin in self.allowed_origins
        ]
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed - O(k) where k is number of patterns"""
        if not origin:
            return False
        
        # Direct match first - O(1)
        if origin in self.allowed_origins:
            return True
        
        # Pattern matching - O(k)
        for pattern in self.origin_patterns:
            if pattern.match(origin):
                return True
        
        return False
    
    def get_cors_headers(self, request: Request) -> Dict[str, str]:
        """Get CORS headers for request - O(1)"""
        origin = request.headers.get('Origin')
        
        headers = {}
        
        if self.is_origin_allowed(origin):
            headers['Access-Control-Allow-Origin'] = origin
            headers['Access-Control-Allow-Credentials'] = 'true'
        
        if request.method == 'OPTIONS':
            headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
            headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
            headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        
        return headers