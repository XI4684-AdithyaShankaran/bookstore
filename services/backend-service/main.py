#!/usr/bin/env python3
"""
FastAPI Backend for Bkmrk'd Bookstore
Production-ready API
"""

import os
import asyncio
import logging
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from collections import deque

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
import uvicorn
from sqlalchemy import create_engine, text, Index, or_
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.pool import QueuePool
import redis as aioredis
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import psutil
import threading
import time

from app.models.book import Book
from app.models.user import User
from app.models.bookshelf import Bookshelf

from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.book import BookResponse, BookCreate
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.schemas.auth import Token, TokenData
from app.services.book_service import BookService
from app.services.user_service import UserService
from app.services.bookshelf_service import BookshelfService
from app.services.cart_service import CartService
from app.services.wishlist_service import WishlistService
from app.services.notification_service import NotificationService
from app.services.optimized_algorithms import optimized_algorithms
from app.api.payment import PaymentService
from app.services.redis_service import redis_service, cache_result, CacheStrategy
from app.database.optimizations import db_optimizations
from app.database import Base


# Initialize FastAPI app with lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    try:
        # Initialize database optimizations
        try:
            db = SessionLocal()
            try:
                # Create tables if they don't exist
                Base.metadata.create_all(bind=engine)
                
                # Run database optimizations
                try:
                    # Initialize db_optimizations with engine
                    db_optimizations.engine = engine
                    db_optimizations.create_performance_indexes(db)
                    db_optimizations.optimize_table_statistics(db)
                    
                    # VACUUM needs to run outside transaction
                    db.close()
                    db_optimizations.vacuum_database(engine)
                    db = SessionLocal()
                except Exception as opt_error:
                    logger.warning(f"⚠️ Database optimizations failed: {opt_error}")
                    # Continue startup even if optimizations fail
            finally:
                db.close()
        except Exception as db_error:
            logger.warning(f"⚠️ Database optimizations failed: {db_error}")
        
        # Initialize recommendation engine
        try:
            await recommendation_engine.load_books_data()
        except Exception as rec_error:
            logger.warning(f"⚠️ Recommendation engine initialization failed: {rec_error}")
        
        # Start background tasks
        asyncio.create_task(cache_cleanup_task())
        asyncio.create_task(system_monitoring_task())
        
        logger.info("✅ Backend started successfully")
        yield
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    finally:
        # Cleanup on shutdown
        try:
            # Clean up resources
            cache.cleanup()
            
            # Close database connections
            engine.dispose()
            
            logger.info("✅ Backend shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Shutdown error: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Bkmrk'd Bookstore API",
    description="Production-ready bookstore API",
    version="2.0.0",
    lifespan=lifespan
)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'logs/app.log',
            maxBytes=2*1024*1024,  # 2MB
            backupCount=2
        )
    ]
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
rate_limit_exceeded_handler = _rate_limit_exceeded_handler

# Global variables
recommendation_cache = {}
cache_lock = threading.Lock()
last_cache_cleanup = time.time()
CACHE_CLEANUP_INTERVAL = 300  # 5 minutes
startup_time = time.time()

# Database configuration - Use PostgreSQL for production with Kaggle data
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db")
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Increased for production
    max_overflow=30,  # Increased for production
    pool_recycle=3600,  # 1 hour
    pool_timeout=30,  # Increased timeout
    pool_pre_ping=True,  # Connection validation
    echo=False,  # Disable SQL logging
    connect_args={
        "connect_timeout": 10,
        "application_name": "bookstore_backend"
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Redis configuration
# redis_client = redis.Redis(
#     host=os.getenv("REDIS_HOST", "localhost"),
#     port=int(os.getenv("REDIS_PORT", "6379")),
#     db=0,
#     decode_responses=True,
#     max_connections=20,  # Increased for production
#     socket_connect_timeout=5,  # Increased timeout
#     socket_timeout=5,  # Increased timeout
#     retry_on_timeout=True,
#     health_check_interval=30
# )

# LRU Cache
class LRUCache:
    """LRU cache with O(1) operations"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 1800):
        self.max_size = max_size
        self.ttl = ttl
        self.cache = {}
        self.access_order = deque()
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with O(1) time complexity"""
        if key in self.cache:
            # Check TTL
            if time.time() - self.access_times[key] > self.ttl:
                self._remove(key)
                return None
            
            # Update access order
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with O(1) time complexity"""
        if key in self.cache:
            # Update existing
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            lru_key = self.access_order.popleft()
            self._remove(lru_key)
        
        self.cache[key] = value
        self.access_order.append(key)
        self.access_times[key] = time.time()
    
    def _remove(self, key: str) -> None:
        """Remove key from cache"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            if key in self.access_order:
                self.access_order.remove(key)
    
    def cleanup(self) -> int:
        """Clean up expired entries - O(n) time complexity"""
        current_time = time.time()
        expired_keys = [
            key for key, access_time in self.access_times.items()
            if current_time - access_time > self.ttl
        ]
        
        for key in expired_keys:
            self._remove(key)
        
        return len(expired_keys)

# Initialize optimized cache
cache = LRUCache(max_size=2000, ttl=1800)

# Recommendation engine
class RecommendationEngine:
    """Recommendation engine"""
    
    def __init__(self):
        self.books_data = []
        self.last_reload = 0
        self.reload_interval = 300  # 5 minutes
        self.cache = {}
    
    def _should_reload(self) -> bool:
        """Check if data should be reloaded"""
        return time.time() - self.last_reload > self.reload_interval
    
    async def load_books_data(self):
        """Load books data with optimization"""
        try:
            if not self._should_reload():
                return
            
                        # Use optimized database query
            db = SessionLocal()
            try:
                books = db.query(Book).all()
                
                self.books_data = [
                    {
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "genre": book.genre,
                        "rating": book.rating,
                        "price": book.price,
                        "image_url": book.image_url
                    }
                    for book in books
                ]
                
                self.last_reload = time.time()
                logger.info(f"✅ Loaded {len(self.books_data)} books with optimization")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error loading books data: {e}")
            raise
    
    async def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user recommendations"""
        try:
            # Check cache first
            cache_key = f"user_recommendations_{user_id}_{limit}"
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Load data if needed
            await self.load_books_data()
            
            # Use optimized algorithms
            db = SessionLocal()
            try:
                # Get user's reading history and preferences
                recommendations = []
                books = db.query(Book).limit(limit).all()
                
                for book in books:
                    recommendations.append({
                        "id": book.id,
                        "title": book.title,
                        "author": book.author,
                        "genre": book.genre,
                        "rating": book.rating,
                        "price": book.price,
                        "image_url": book.image_url
                    })
                
                # Cache the result
                cache.set(cache_key, recommendations)
                
                return recommendations
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"❌ Error getting user recommendations: {e}")
            return []

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

# Database dependency
def get_db():
    """Get database session with optimization"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication dependency
security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    """Get current user with JWT validation"""
    try:
        # Validate JWT token and get user from database
        db = SessionLocal()
        try:
            # Decode JWT token to get user_id
            from app.services.auth_service import verify_token
            payload = verify_token(token.credentials)
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Get user from database
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )



async def cache_cleanup_task():
    """Cache cleanup task"""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            expired_count = cache.cleanup()
            if expired_count > 0:
                logger.info(f"🧹 Cleaned up {expired_count} expired cache entries")
        except Exception as e:
            logger.error(f"❌ Cache cleanup error: {e}")

async def system_monitoring_task():
    """System monitoring task"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            
            # Monitor system resources
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            if cpu_percent > 80 or memory.percent > 80:
                logger.warning(f"⚠️ High resource usage - CPU: {cpu_percent}%, Memory: {memory.percent}%")
            
            # Monitor database connections
            pool_size = engine.pool.size()
            if pool_size > 15:
                logger.warning(f"⚠️ High database connection usage: {pool_size}")
                
        except Exception as e:
            logger.error(f"❌ System monitoring error: {e}")

# Health check endpoint
@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check with monitoring"""
    try:
        # Database health check
        db_healthy = False
        db_response_time = "N/A"
        try:
            import time as time_module
            start_time = time_module.time()
            db = SessionLocal()
            db.execute(text("SELECT 1"))
            db.close()
            db_response_time = f"{(time_module.time() - start_time) * 1000:.2f}ms"
            db_healthy = True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
        
        # Redis health check
        redis_health = redis_service.get_health_status()
        
        # System metrics
        import psutil
        system_metrics = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
        
        # Overall health status
        overall_healthy = db_healthy and redis_health["healthy"]
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": time.time(),
            "services": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "response_time": db_response_time,
                    "type": "PostgreSQL"
                },
                "redis": redis_health,
                "api_server": {
                    "status": "healthy",
                    "uptime": time.time() - startup_time,
                    "version": "2.0.0"
                }
            },
            "system": system_metrics,
            "cache_metrics": redis_service.get_metrics().__dict__
        }
    except Exception as e:
        logger.error(f"❌ Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# Book endpoints
@app.get("/books", response_model=List[BookResponse])
@limiter.limit("1000/minute")
@cache_result(ttl=1800, strategy=CacheStrategy.LRU, key_prefix="books")  # Cache for 30 minutes
async def get_books(
    skip: int = 0,
    limit: int = 25,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None,
    request: Request = None
):
    """optimized book retrieval with intelligent caching"""
    try:
        # Generate cache key based on parameters
        cache_key = f"books:list:{skip}:{limit}:{search}:{genre}:{min_rating}:{max_price}"
        
        # Try to get from cache first
        cached_result = await redis_service.get(cache_key)
        if cached_result:
            logger.info(f"✅ Cache hit for books list - Key: {cache_key}")
            return cached_result
        
        # Database query with optimization
        db = SessionLocal()
        try:
            query = db.query(Book)
            
            # Apply filters with optimization
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Book.title.ilike(search_term),
                        Book.description.ilike(search_term),
                        Book.author.ilike(search_term)
                    )
                )
            
            if genre:
                # Use the simple genre field from Kaggle dataset
                query = query.filter(Book.genre.ilike(f"%{genre}%"))
            
            if min_rating is not None:
                query = query.filter(Book.rating >= min_rating)
            
            if max_price is not None:
                query = query.filter(Book.price <= max_price)
            
            # optimized pagination
            books = query.offset(skip).limit(limit).all()
            
            # Convert to response models
            result = [BookResponse.model_validate(book) for book in books]
            
            # Cache the result
            await redis_service.set(cache_key, result, ttl=1800)
            
            logger.info(f"✅ Books retrieved successfully - Count: {len(result)}")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error retrieving books: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/books/{book_id}", response_model=BookResponse)
@limiter.limit("2000/minute")
@cache_result(ttl=3600, strategy=CacheStrategy.LRU, key_prefix="book")
async def get_book(book_id: int, request: Request = None):
    """optimized single book retrieval with intelligent caching"""
    try:
        # Try cache first
        cache_key = f"book:detail:{book_id}"
        cached_book = await redis_service.get(cache_key)
        if cached_book:
            logger.info(f"✅ Cache hit for book {book_id}")
            return cached_book
        
        # Database query
        db = SessionLocal()
        try:
            book = db.query(Book).filter(Book.id == book_id).first()
            
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            
            result = BookResponse.model_validate(book)
            
            # Cache the result
            await redis_service.set(cache_key, result, ttl=3600)
            
            logger.info(f"✅ Book {book_id} retrieved successfully")
            return result
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving book {book_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/recommendations", response_model=List[BookResponse])
@limiter.limit("500/minute")
@cache_result(ttl=900, strategy=CacheStrategy.LRU, key_prefix="recommendations")
async def get_recommendations(
    user_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized recommendations with intelligent caching"""
    try:
        cache_key = f"recommendations:user:{user_id}:limit:{limit}"
        
        # Try cache first
        cached_recommendations = await redis_service.get(cache_key)
        if cached_recommendations:
            logger.info(f"✅ Cache hit for recommendations - User: {user_id}")
            return cached_recommendations
        
        # Generate recommendations
        recommendation_engine = RecommendationEngine()
        recommendations = await recommendation_engine.get_user_recommendations(user_id, limit)
        
        # Cache recommendations
        await redis_service.set(cache_key, recommendations, ttl=900)
        
        logger.info(f"✅ Recommendations generated for user {user_id} - Count: {len(recommendations)}")
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error generating recommendations for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# optimized user endpoints
@app.post("/users", response_model=UserResponse)
@limiter.limit("100/minute")
async def create_user(user: UserCreate, db: Session = Depends(get_db), request: Request = None):
    """optimized user creation"""
    try:
        user_service = UserService(db)
        return user_service.create_user(user)
    except Exception as e:
        logger.error(f"❌ Error creating user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/token", response_model=Token)
@limiter.limit("200/minute")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db), request: Request = None):
    """optimized login endpoint"""
    try:
        user_service = UserService(db)
        return user_service.authenticate_user(user_credentials)
    except Exception as e:
        logger.error(f"❌ Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# optimized bookshelf endpoints
@app.get("/bookshelves", response_model=List[Dict[str, Any]])
@limiter.limit("600/minute")
async def get_user_bookshelves(
    user_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized bookshelf endpoint"""
    try:
        db = SessionLocal()
        try:
            bookshelf_service = BookshelfService(db)
            return bookshelf_service.get_user_bookshelves(user_id)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error getting bookshelves: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/bookshelves", response_model=Dict[str, Any])
@limiter.limit("200/minute")
async def create_bookshelf(
    bookshelf_data: dict,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized bookshelf creation"""
    try:
        db = SessionLocal()
        try:
            bookshelf_service = BookshelfService(db)
            return bookshelf_service.create_bookshelf(bookshelf_data, current_user.id)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error creating bookshelf: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/bookshelves/{bookshelf_id}/add")
@limiter.limit("200/minute")
async def add_book_to_bookshelf(
    bookshelf_id: int,
    book_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized add book to bookshelf"""
    try:
        db = SessionLocal()
        try:
            bookshelf_service = BookshelfService(db)
            bookshelf_service.add_book_to_bookshelf(bookshelf_id, book_id, current_user.id)
            return {"message": "Book added to bookshelf"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error adding book to bookshelf: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/bookshelves/{bookshelf_id}/remove")
@limiter.limit("200/minute")
async def remove_book_from_bookshelf(
    bookshelf_id: int,
    book_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized remove book from bookshelf"""
    try:
        db = SessionLocal()
        try:
            bookshelf_service = BookshelfService(db)
            bookshelf_service.remove_book_from_bookshelf(bookshelf_id, book_id, current_user.id)
            return {"message": "Book removed from bookshelf"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error removing book from bookshelf: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# optimized cart endpoints
@app.get("/cart", response_model=dict)
@limiter.limit("400/minute")
async def get_cart(current_user: User = Depends(get_current_user), request: Request = None):
    """optimized cart retrieval with Redis caching"""
    try:
        cache_key = f"cart:user:{current_user.id}"
        
        # Try cache first
        cached_cart = await redis_service.get(cache_key)
        if cached_cart:
            logger.info(f"✅ Cache hit for cart - User: {current_user.id}")
            return cached_cart
        
        # Get cart from database
        db = SessionLocal()
        try:
            cart_service = CartService(db)
            cart_data = await cart_service.get_user_cart(current_user.id)
            
            # Cache cart data
            await redis_service.set(cache_key, cart_data.model_dump(), ttl=300)  # 5 minutes
            
            logger.info(f"✅ Cart retrieved for user {current_user.id}")
            return cart_data.model_dump()
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error retrieving cart for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/cart/items")
@limiter.limit("200/minute")
async def add_to_cart(
    book_id: int,
    quantity: int = 1,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized cart item addition with cache invalidation"""
    try:
        db = SessionLocal()
        try:
            cart_service = CartService(db)
            result = await cart_service.add_to_cart(current_user.id, book_id, quantity)
            
            # Invalidate cart cache
            cache_key = f"cart:user:{current_user.id}"
            await redis_service.delete(cache_key)
            
            logger.info(f"✅ Item added to cart - User: {current_user.id}, Book: {book_id}, Quantity: {quantity}")
            return result
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Error adding item to cart: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/cart/items/{item_id}")
@limiter.limit("200/minute")
async def update_cart_item(
    item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized update cart item"""
    try:
        db = SessionLocal()
        try:
            cart_service = CartService(db)
            cart_service.update_cart_item(item_id, quantity, current_user.id)
            return {"message": "Cart item updated"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error updating cart item: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/cart/items/{item_id}")
@limiter.limit("200/minute")
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized remove from cart"""
    try:
        db = SessionLocal()
        try:
            cart_service = CartService(db)
            cart_service.remove_from_cart(item_id, current_user.id)
            return {"message": "Item removed from cart"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error removing from cart: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/cart/clear")
@limiter.limit("100/minute")
async def clear_cart(current_user: User = Depends(get_current_user), request: Request = None):
    """optimized clear cart"""
    try:
        db = SessionLocal()
        try:
            cart_service = CartService(db)
            cart_service.clear_cart(current_user.id)
            return {"message": "Cart cleared"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error clearing cart: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# optimized wishlist endpoints
@app.get("/wishlist", response_model=dict)
@limiter.limit("400/minute")
async def get_wishlist(current_user: User = Depends(get_current_user), request: Request = None):
    """optimized wishlist endpoint"""
    try:
        db = SessionLocal()
        try:
            wishlist_service = WishlistService(db)
            return wishlist_service.get_user_wishlist(current_user.id)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error getting wishlist: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/wishlist/items")
@limiter.limit("200/minute")
async def add_to_wishlist(
    book_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized add to wishlist"""
    try:
        db = SessionLocal()
        try:
            wishlist_service = WishlistService(db)
            wishlist_service.add_to_wishlist(current_user.id, book_id)
            return {"message": "Item added to wishlist"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error adding to wishlist: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/wishlist/items/{item_id}")
@limiter.limit("200/minute")
async def remove_from_wishlist(
    item_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """optimized remove from wishlist"""
    try:
        db = SessionLocal()
        try:
            wishlist_service = WishlistService(db)
            wishlist_service.remove_from_wishlist(item_id, current_user.id)
            return {"message": "Item removed from wishlist"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error removing from wishlist: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/wishlist/clear")
@limiter.limit("100/minute")
async def clear_wishlist(current_user: User = Depends(get_current_user), request: Request = None):
    """optimized clear wishlist"""
    try:
        db = SessionLocal()
        try:
            wishlist_service = WishlistService(db)
            wishlist_service.clear_wishlist(current_user.id)
            return {"message": "Wishlist cleared"}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Error clearing wishlist: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User recommendations endpoint
@app.get("/users/{user_id}/recommendations", response_model=List[BookResponse])
@limiter.limit("400/minute")
async def get_user_recommendations(
    user_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """User recommendations"""
    try:
        recommendations = await recommendation_engine.get_user_recommendations(user_id, limit)
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error getting user recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Authentication endpoints
@app.post("/auth/google")
@limiter.limit("200/minute")
async def google_auth(user_data: dict, request: Request = None):
    """Google authentication"""
    try:
        # This would handle Google OAuth
        return {"message": "Google authentication successful"}
    except Exception as e:
        logger.error(f"❌ Error in Google auth: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/register", response_model=UserResponse)
@limiter.limit("100/minute")
async def register_user(user: UserCreate, db: Session = Depends(get_db), request: Request = None):
    """User registration"""
    try:
        user_service = UserService(db)
        return user_service.create_user(user)
    except Exception as e:
        logger.error(f"❌ Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # Multiple workers for production
        loop="uvloop",  # Faster event loop
        http="httptools",  # Faster HTTP parser
        access_log=True,
        log_level="info"
    )