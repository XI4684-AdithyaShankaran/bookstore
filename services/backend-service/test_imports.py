#!/usr/bin/env python3
"""
Simple import test for backend service
"""

# Test basic imports
try:
    from fastapi import FastAPI, HTTPException, Depends, status, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer
    from pydantic import BaseModel
    import uvicorn
    from sqlalchemy import create_engine, text, Index, or_
    from sqlalchemy.orm import sessionmaker, Session, joinedload
    from sqlalchemy.pool import QueuePool
    import redis.asyncio as aioredis
    import redis
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    import psutil
    import threading
    import time
    print("✅ Basic imports successful")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    exit(1)

# Test app imports
try:
    from app.models.book import Book
    from app.models.user import User
    from app.models.bookshelf import Bookshelf
    from app.models.payment import Payment, PaymentStatus, PaymentMethod
    from app.models.order import Order, OrderItem, OrderStatus
    print("✅ Model imports successful")
except Exception as e:
    print(f"❌ Model imports failed: {e}")
    exit(1)

# Test schema imports
try:
    from app.schemas.book import BookResponse, BookCreate
    from app.schemas.user import UserCreate, UserResponse, UserLogin
    from app.schemas.auth import Token, TokenData
    print("✅ Schema imports successful")
except Exception as e:
    print(f"❌ Schema imports failed: {e}")
    exit(1)

# Test service imports
try:
    from app.services.book_service import BookService
    from app.services.user_service import UserService
    from app.services.bookshelf_service import BookshelfService
    from app.services.cart_service import CartService
    from app.services.wishlist_service import WishlistService
    from app.services.notification_service import NotificationService
    from app.services.optimized_algorithms import optimized_algorithms
    from app.api.payment import PaymentService
    from app.services.redis_service import redis_service, cache_result, CacheStrategy
    print("✅ Service imports successful")
except Exception as e:
    print(f"❌ Service imports failed: {e}")
    exit(1)

print("✅ All imports successful!") 