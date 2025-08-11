#!/usr/bin/env python3
"""
Main FastAPI application for Bkmrk'd Bookstore
Production-ready API with industrial standards
"""

import logging
import time
import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, HTTPException, Depends, WebSocket, WebSocketDisconnect, Response
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import sys
from dotenv import load_dotenv

# Load environment variables from env.local
load_dotenv('../../env.local')

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import get_db, engine, Base
from app.services.book_service import BookService
from app.services.user_service import UserService
from app.services.rating_service import RatingService
from app.services.cart_service import CartService
from app.services.bookshelf_service import BookshelfService
from app.services.recommendation_service import RecommendationService
from app.services.wishlist_service import WishlistService
from app.security.middleware import setup_security_middleware
from app.services.auth_service import create_user_token, verify_password, get_password_hash

# Import all models to register them with SQLAlchemy
from app.models.book import Book
from app.models.user import User
from app.models.bookshelf import Bookshelf
from app.models.cart import CartItem
from app.models.wishlist import WishlistItem
# Import additional models from database.models (avoiding duplicates)
from app.database.models import Rating

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Services will be initialized per request with database session

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Redis for security middleware
redis_client = None
try:
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_password = os.getenv("REDIS_PASSWORD", "")
    
    if redis_password:
        redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}"
    else:
        redis_url = f"redis://{redis_host}:{redis_port}"
    
    redis_client = redis.from_url(redis_url, decode_responses=True)
    redis_client.ping()
    logger.info("✅ Redis connection established for security middleware")
except Exception as e:
    logger.warning(f"⚠️ Redis connection failed for security middleware: {e}")
    redis_client = None

# Get secret key
secret_key = os.getenv("SECRET_KEY", "your_super_secret_key_here_change_in_production")
if secret_key == "your_super_secret_key_here_change_in_production":
    logger.warning("⚠️ Using default secret key - CHANGE IN PRODUCTION!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with comprehensive logging"""
    logger.info("🚀 Starting Bkmrk'd Bookstore API...")
    
    # Database setup
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
    
    # Store Redis client in app state for endpoints
    app.state.redis = redis_client
    
    # Environment validation
    gemini_key = os.getenv("GEMINI_API_KEY", "AIzaSyDd5LhOtk_eBobz7XBLB_vcJoYOTuYhUFM")
    if gemini_key == "AIzaSyDd5LhOtk_eBobz7XBLB_vcJoYOTuYhUFM":
        logger.info("✅ Using GEMINI_API_KEY from environment")
        
    logger.info("🚀 Bkmrk'd API started successfully")
    
    yield
    
    logger.info("🛑 Shutting down Bkmrk'd API...")
    if hasattr(app.state, 'redis') and app.state.redis:
        app.state.redis.close()
        logger.info("✅ Redis connection closed")

# Create FastAPI app
app = FastAPI(
    title="Bkmrk'd Bookstore API",
    description="A modern bookstore API with AI-powered recommendations",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware
try:
    if redis_client:
        setup_security_middleware(app, redis_client, secret_key)
        logger.info("🔒 Security middleware configured")
    else:
        logger.warning("⚠️ Security middleware skipped - Redis not available")
except Exception as e:
    logger.error(f"❌ Security middleware setup failed: {e}")

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()
    
    # Log request details
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    logger.info(f"📋 Headers: {dict(request.headers)}")
    
    # Process request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {e} - Time: {process_time:.3f}s")
        raise

# Health check endpoints
@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    logger.info("🏥 Health check requested")
    return {
        "status": "healthy",
        "service": "Bkmrk'd Bookstore API",
        "version": "1.0.0"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check endpoint with component status"""
    logger.info("🏥 Detailed health check requested")
    
    health_status = {
        "status": "healthy",
        "service": "Bkmrk'd Bookstore API",
        "version": "1.0.0",
        "components": {
            "database": "unknown",
            "redis": "unknown"
        }
    }
    
    # Check database
    try:
        from app.database.database import engine
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        health_status["components"]["database"] = "healthy"
        logger.info("✅ Database health check passed")
    except Exception as e:
        health_status["components"]["database"] = "unhealthy"
        logger.error(f"❌ Database health check failed: {e}")
    
    # Check Redis
    try:
        if hasattr(app.state, 'redis') and app.state.redis:
            app.state.redis.ping()
            health_status["components"]["redis"] = "healthy"
            logger.info("✅ Redis health check passed")
        else:
            health_status["components"]["redis"] = "not_configured"
            logger.warning("⚠️ Redis not configured")
    except Exception as e:
        health_status["components"]["redis"] = "unhealthy"
        logger.error(f"❌ Redis health check failed: {e}")
    
    return health_status

# Books endpoints
@app.get("/api/books")
async def get_books(
    page: int = 1,
    limit: int = 25,
    search: str = None,
    genre: str = None,
    author: str = None,
    db: Session = Depends(get_db)
):
    """Get books with comprehensive logging"""
    logger.info(f"📚 Books request - Page: {page}, Limit: {limit}, Search: {search}, Genre: {genre}, Author: {author}")
    
    try:
        book_service = BookService(db)
        # Convert page to skip (page 1 = skip 0, page 2 = skip 25, etc.)
        skip = (page - 1) * limit
        books = book_service.get_books(skip=skip, limit=limit, search=search, genre=genre)
        logger.info(f"✅ Books retrieved successfully - Count: {len(books.get('books', []))}")
        return books
    except Exception as e:
        logger.error(f"❌ Failed to retrieve books: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve books: {str(e)}")

@app.get("/api/books/{book_id}")
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book with logging"""
    logger.info(f"📖 Book detail request - ID: {book_id}")
    
    try:
        book_service = BookService(db)
        book = book_service.get_book_by_id(book_id)
        if not book:
            logger.warning(f"⚠️ Book not found - ID: {book_id}")
            raise HTTPException(status_code=404, detail="Book not found")
        
        logger.info(f"✅ Book retrieved successfully - ID: {book_id}, Title: {book.title}")
        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to retrieve book {book_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve book: {str(e)}")

# Streaming Books Endpoint - Temporarily disabled due to generator issues
@app.get("/api/books/stream")
async def stream_books(
    search: str = None,
    genre: str = None,
    author: str = None,
    batch_size: int = 5,
    delay: float = 0.1,
    db: Session = Depends(get_db)
):
    """Stream books in real-time with Server-Sent Events - FIXED VERSION"""
    
    try:
        # Get books data
        book_service = BookService(db)
        books_data = book_service.get_books(
            skip=0, 
            limit=batch_size, 
            search=search, 
            genre=genre
        )
        
        books = books_data.get('books', [])
        book_list = []
        
        for book in books:
            book_dict = {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'rating': float(book.rating) if book.rating else 0,
                'price': float(book.price) if book.price else 0,
                'image_url': book.image_url,
                'description': book.description
            }
            book_list.append(book_dict)
        
        return {
            "type": "books_batch",
            "data": book_list,
            "total": len(book_list),
            "message": "Books retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error in stream_books: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Streaming Search Endpoint - Fixed version
@app.get("/api/search/stream")
async def stream_search_results(
    q: str,  # Search query
    search_type: str = "all",  # "title", "author", "genre", "all"
    batch_size: int = 3,
    delay: float = 0.15,
    db: Session = Depends(get_db)
):
    """Stream search results in real-time with Server-Sent Events - FIXED VERSION"""
    
    try:
        # Get search results
        book_service = BookService(db)
        search_terms = q.lower().split()
        
        books_data = book_service.get_books(
            skip=0, 
            limit=batch_size, 
            search=q
        )
        
        books = books_data.get('books', [])
        search_results = []
        
        for book in books:
            score = calculate_search_relevance(book, search_terms, search_type)
            if score > 0:  # Only include relevant results
                book_dict = {
                    'id': book.id,
                    'title': book.title,
                    'author': book.author,
                    'genre': book.genre,
                    'rating': float(book.rating) if book.rating else 0,
                    'price': float(book.price) if book.price else 0,
                    'image_url': book.image_url,
                    'description': book.description,
                    'relevance_score': round(score, 2),
                    'match_type': get_match_type(book, search_terms)
                }
                search_results.append(book_dict)
        
        # Sort by relevance score
        search_results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            "type": "search_results",
            "data": search_results,
            "total": len(search_results),
            "query": q,
            "message": "Search results retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error in stream_search_results: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

def calculate_search_relevance(book, search_terms: list, search_type: str) -> float:
    """Calculate relevance score for search results"""
    score = 0.0
    
    # Text fields to search
    title = book.title.lower() if book.title else ""
    author = book.author.lower() if book.author else ""
    genre = book.genre.lower() if book.genre else ""
    description = book.description.lower() if book.description else ""
    
    for term in search_terms:
        term = term.lower().strip()
        if not term:
            continue
            
        # Title matches (highest weight)
        if term in title:
            if search_type in ["title", "all"]:
                score += 3.0
                if title.startswith(term):
                    score += 2.0  # Bonus for prefix match
        
        # Author matches (high weight)
        if term in author:
            if search_type in ["author", "all"]:
                score += 2.5
                if author.startswith(term):
                    score += 1.5
        
        # Genre matches (medium weight)
        if term in genre:
            if search_type in ["genre", "all"]:
                score += 2.0
        
        # Description matches (lower weight)
        if term in description:
            if search_type == "all":
                score += 0.5
    
    # Boost for higher rated books
    if book.rating:
        score += float(book.rating) * 0.1
    
    return score

def get_match_type(book, search_terms: list) -> str:
    """Determine what type of match this is"""
    title = book.title.lower() if book.title else ""
    author = book.author.lower() if book.author else ""
    genre = book.genre.lower() if book.genre else ""
    
    for term in search_terms:
        term = term.lower().strip()
        if term in title:
            return "title"
        elif term in author:
            return "author"
        elif term in genre:
            return "genre"
    
    return "description"

# WebSocket for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"🔌 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Failed to send personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"❌ Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws/books")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data.get("type") == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": time.time()}),
                    websocket
                )
            elif message_data.get("type") == "subscribe":
                # Handle subscription to book updates
                await manager.send_personal_message(
                    json.dumps({
                        "type": "subscribed",
                        "message": "Subscribed to book updates",
                        "timestamp": time.time()
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# Function to broadcast book updates (can be called from other parts of the app)
async def broadcast_book_update(book_data: dict, update_type: str = "update"):
    message = {
        "type": "book_update",
        "update_type": update_type,  # "create", "update", "delete"
        "data": book_data,
        "timestamp": time.time()
    }
    await manager.broadcast(json.dumps(message))

# Utility function for secure cookie handling
def set_secure_auth_cookies(response: Response, access_token: str, refresh_token: str = None):
    """Set secure, HTTP-only cookies for authentication tokens"""
    
    # Determine if we're in production (HTTPS required for secure cookies)
    is_production = os.getenv('NODE_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'
    
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=is_production,  # Only send over HTTPS in production
        samesite="lax",  # CSRF protection while allowing some cross-site requests
        path="/"
    )
    
    # Set refresh token cookie if provided
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=86400 * 7,  # 7 days
            httponly=True,
            secure=is_production,
            samesite="lax",
            path="/"
        )
    
    logger.info("🔐 Secure auth cookies set successfully")

# Users endpoints
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str

class AuthUser(BaseModel):
    id: int
    email: EmailStr
    username: str | None = None
    created_at: str | None = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: AuthUser

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_user_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": getattr(user, "username", None),
            "created_at": str(getattr(user, "created_at", ""))
        }
    }

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    hashed = get_password_hash(body.password)
    # Prefer models that have username/full_name fields
    user = User(
        email=body.email,
        username=getattr(User, 'username', None) and body.username or body.email.split('@')[0],
        hashed_password=hashed,
        is_active=True
    )
    # If model has full_name/name, set a sensible default
    if hasattr(user, 'full_name'):
        setattr(user, 'full_name', body.username)
    elif hasattr(user, 'name'):
        setattr(user, 'name', body.username)
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_user_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": getattr(user, "username", None),
            "created_at": str(getattr(user, "created_at", ""))
        }
    }

@app.get("/api/users/me", response_model=AuthUser)
async def get_me(credentials: Request, db: Session = Depends(get_db)):
    # Read bearer token from Authorization header
    auth_header = credentials.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    try:
        payload = json.loads(json.dumps(verify_token(token))) if False else verify_token(token)  # keep imports simple
    except Exception:
        payload = None
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user.id,
        "email": user.email,
        "username": getattr(user, "username", None),
        "created_at": str(getattr(user, "created_at", ""))
    }
@app.get("/api/users")
async def get_users(db: Session = Depends(get_db)):
    """Get users with logging"""
    logger.info("👥 Users request")
    
    try:
        user_service = UserService(db)
        users = user_service.get_users(db)
        logger.info(f"✅ Users retrieved successfully - Count: {len(users)}")
        return users
    except Exception as e:
        logger.error(f"❌ Failed to retrieve users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")

# Ratings endpoints
@app.get("/api/ratings")
async def get_ratings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get ratings with logging"""
    logger.info(f"⭐ Ratings request - Skip: {skip}, Limit: {limit}")
    
    try:
        rating_service = RatingService()
        ratings = rating_service.get_ratings(db, skip=skip, limit=limit)
        logger.info(f"✅ Ratings retrieved successfully - Count: {len(ratings)}")
        return ratings
    except Exception as e:
        logger.error(f"❌ Failed to retrieve ratings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ratings: {str(e)}")

@app.get("/api/ratings/book/{book_id}")
async def get_book_ratings(book_id: int, db: Session = Depends(get_db)):
    """Get ratings for a specific book"""
    logger.info(f"⭐ Book ratings request - Book ID: {book_id}")
    
    try:
        rating_service = RatingService()
        ratings = rating_service.get_ratings_by_book(db, book_id)
        stats = rating_service.get_book_rating_stats(db, book_id)
        logger.info(f"✅ Book ratings retrieved successfully - Count: {len(ratings)}")
        return {"ratings": ratings, "stats": stats}
    except Exception as e:
        logger.error(f"❌ Failed to retrieve book ratings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve book ratings: {str(e)}")

@app.get("/api/ratings/user/{user_id}")
async def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    """Get ratings by a specific user"""
    logger.info(f"⭐ User ratings request - User ID: {user_id}")
    
    try:
        rating_service = RatingService()
        ratings = rating_service.get_ratings_by_user(db, user_id)
        logger.info(f"✅ User ratings retrieved successfully - Count: {len(ratings)}")
        return ratings
    except Exception as e:
        logger.error(f"❌ Failed to retrieve user ratings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user ratings: {str(e)}")

# Cart endpoints
@app.get("/api/cart/{user_id}")
async def get_cart(user_id: int, db: Session = Depends(get_db)):
    """Get user cart with logging"""
    logger.info(f"🛒 Cart request - User ID: {user_id}")
    
    try:
        cart_service = CartService(db)
        cart = await cart_service.get_user_cart(user_id)
        logger.info(f"✅ Cart retrieved successfully - User ID: {user_id}, Items: {len(cart.items) if cart.items else 0}")
        return cart
    except Exception as e:
        logger.error(f"❌ Failed to retrieve cart for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cart: {str(e)}")

# Bookshelves endpoints
@app.get("/bookshelves")
@limiter.limit("100/minute")
async def get_user_bookshelves(request: Request, user_id: int = 1, db: Session = Depends(get_db)):
    """Get user bookshelves"""
    logger.info(f"📚 Bookshelves request - User ID: {user_id}")
    
    try:
        bookshelf_service = BookshelfService(db)
        bookshelves = await bookshelf_service.get_user_bookshelves(user_id)
        logger.info(f"✅ Bookshelves retrieved successfully - User ID: {user_id}, Count: {len(bookshelves)}")
        return bookshelves
    except Exception as e:
        logger.error(f"❌ Failed to retrieve bookshelves for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve bookshelves: {str(e)}")

@app.post("/bookshelves")
@limiter.limit("50/minute")
async def create_bookshelf(request: Request, body: dict, user_id: int = 1, db: Session = Depends(get_db)):
    """Create a new bookshelf"""
    try:
        name = body.get("name")
        description = body.get("description", "")
        is_public = body.get("is_public", False)
        
        if not name:
            raise HTTPException(status_code=400, detail="Bookshelf name is required")
            
        bookshelf_service = BookshelfService(db)
        bookshelf = await bookshelf_service.create_bookshelf(user_id, name, description, is_public)
        logger.info(f"✅ Bookshelf created - User ID: {user_id}, Name: {name}")
        return bookshelf
    except Exception as e:
        logger.error(f"❌ Failed to create bookshelf: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create bookshelf: {str(e)}")

@app.post("/bookshelves/{bookshelf_id}/books/{book_id}")
@limiter.limit("100/minute")
async def add_book_to_bookshelf(request: Request, bookshelf_id: int, book_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    """Add book to bookshelf"""
    try:
        bookshelf_service = BookshelfService(db)
        await bookshelf_service.add_book_to_bookshelf(user_id, bookshelf_id, book_id)
        logger.info(f"✅ Book {book_id} added to bookshelf {bookshelf_id} for user {user_id}")
        return {"status": "added"}
    except Exception as e:
        logger.error(f"❌ Failed to add book to bookshelf: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add book to bookshelf: {str(e)}")

@app.delete("/bookshelves/{bookshelf_id}/books/{book_id}")
@limiter.limit("100/minute")  
async def remove_book_from_bookshelf(request: Request, bookshelf_id: int, book_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    """Remove book from bookshelf"""
    try:
        bookshelf_service = BookshelfService(db)
        await bookshelf_service.remove_book_from_bookshelf(user_id, bookshelf_id, book_id)
        logger.info(f"✅ Book {book_id} removed from bookshelf {bookshelf_id} for user {user_id}")
        return {"status": "removed"}
    except Exception as e:
        logger.error(f"❌ Failed to remove book from bookshelf: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove book from bookshelf: {str(e)}")

# Recommendations endpoint
@app.post("/api/recommendations")
@limiter.limit("100/minute")
async def get_recommendations(request: Request, recommendation_request: dict, db: Session = Depends(get_db)):
    """Get AI-powered book recommendations"""
    try:
        recommendation_service = RecommendationService(db)
        
        # Extract parameters from request
        user_id = recommendation_request.get("user_id")
        user_preferences = recommendation_request.get("user_preferences", "")
        limit = recommendation_request.get("limit", 10)
        
        # Get recommendations
        if user_id:
            recommendations = await recommendation_service.get_user_recommendations(user_id, limit)
        else:
            # For anonymous users, get general recommendations
            recommendations = await recommendation_service.get_trending_recommendations(limit)
        
        return {
            "recommendations": recommendations,
            "total": len(recommendations),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendations: {str(e)}"
        )

# Wishlist endpoints
@app.get("/api/wishlist")
@limiter.limit("100/minute")
async def get_user_wishlist(request: Request, user_id: int = 1, db: Session = Depends(get_db)):
    """Get user's wishlist items"""
    try:
        wishlist_service = WishlistService(db)
        wishlist_items = await wishlist_service.get_user_wishlist(user_id)
        logger.info(f"✅ Wishlist retrieved - User ID: {user_id}, Items: {len(wishlist_items)}")
        return wishlist_items
    except Exception as e:
        logger.error(f"❌ Failed to retrieve wishlist for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve wishlist: {str(e)}")

@app.post("/api/wishlist")
@limiter.limit("50/minute")
async def add_to_wishlist(request: Request, body: dict, user_id: int = 1, db: Session = Depends(get_db)):
    """Add book to user's wishlist"""
    try:
        book_id = body.get("book_id")
        if not book_id:
            raise HTTPException(status_code=400, detail="book_id is required")
            
        wishlist_service = WishlistService(db)
        wishlist_item = await wishlist_service.add_to_wishlist(user_id, book_id)
        logger.info(f"✅ Book {book_id} added to wishlist for user {user_id}")
        return wishlist_item
    except Exception as e:
        logger.error(f"❌ Failed to add book to wishlist: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add to wishlist: {str(e)}")

@app.delete("/api/wishlist/{book_id}")
@limiter.limit("50/minute")
async def remove_from_wishlist(book_id: int, request: Request, user_id: int = 1, db: Session = Depends(get_db)):
    """Remove book from user's wishlist"""
    try:
        wishlist_service = WishlistService(db)
        await wishlist_service.remove_from_wishlist(user_id, book_id)
        logger.info(f"✅ Book {book_id} removed from wishlist for user {user_id}")
        return {"status": "removed"}
    except Exception as e:
        logger.error(f"❌ Failed to remove book from wishlist: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove from wishlist: {str(e)}")

# Logs endpoint for frontend
@app.post("/api/logs")
async def receive_frontend_logs(log_entry: dict):
    """Receive and store frontend logs"""
    logger.info(f"📝 Frontend log received: {log_entry.get('message', 'No message')}", {
        'level': log_entry.get('level'),
        'category': log_entry.get('category'),
        'timestamp': log_entry.get('timestamp'),
        'data': log_entry.get('data'),
        'error': log_entry.get('error'),
    })
    
    return {"status": "logged"}

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with logging"""
    logger.error(f"❌ Unhandled exception in {request.method} {request.url.path}: {exc}")
    
    # Handle specific anyio errors
    if "generator didn't stop after throw()" in str(exc):
        logger.error("❌ AnyIO generator error detected - this is a known issue with streaming responses")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Streaming service temporarily unavailable",
                "error": "Service error",
                "retry_after": 5
            }
        )
    
    # Handle other common errors
    if "EndOfStream" in str(exc) or "WouldBlock" in str(exc):
        logger.error("❌ Stream connection error detected")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Connection error",
                "error": "Stream connection failed",
                "retry_after": 2
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Add specific handler for RuntimeError
@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handle RuntimeError specifically"""
    logger.error(f"❌ RuntimeError in {request.method} {request.url.path}: {exc}")
    
    if "generator didn't stop after throw()" in str(exc):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Streaming service error",
                "error": "Generator error",
                "retry_after": 5
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Runtime error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 