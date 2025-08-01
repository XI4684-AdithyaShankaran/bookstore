#!/usr/bin/env python3
"""
Main FastAPI application for Bkmrk'd Bookstore
Production-ready API with industrial standards
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session

from app.database import get_db, create_tables
from app.services.auth_service import get_current_user
from app.services.book_service import UltraOptimizedBookService
from app.services.cart_service import UltraOptimizedCartService
from app.services.user_service import UltraOptimizedUserService
from app.services.bookshelf_service import UltraOptimizedBookshelfService
from app.api.payment import router as payment_router
from app.models.user import User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Bkmrk'd Bookstore API...")
    try:
        # Create database tables
        create_tables()
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Bkmrk'd Bookstore API...")

# Create FastAPI app
app = FastAPI(
    title="Bkmrk'd Bookstore API",
    description="Production-ready bookstore API with industrial standards",
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

# Include routers
app.include_router(payment_router, prefix="/api")

# Health check endpoint
@app.get("/health")
@limiter.limit("100/minute")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "Bkmrk'd Bookstore API",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

# Book endpoints
@app.get("/api/books")
@limiter.limit("1000/minute")
async def get_books(
    skip: int = 0,
    limit: int = 25,
    search: str = None,
    genre: str = None,
    min_rating: float = None,
    max_price: float = None,
    db: Session = Depends(get_db)
):
    """Get books with filtering and pagination"""
    try:
        book_service = UltraOptimizedBookService(db)
        result = book_service.get_books_ultra_optimized(
            skip=skip,
            limit=limit,
            search=search,
            genre=genre,
            min_rating=min_rating,
            max_price=max_price
        )
        return result
    except Exception as e:
        logger.error(f"Error getting books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve books"
        )

@app.get("/api/books/{book_id}")
@limiter.limit("1000/minute")
async def get_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Get book by ID"""
    try:
        book_service = UltraOptimizedBookService(db)
        book = book_service.get_book_by_id(book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
        return book
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve book"
        )

# Cart endpoints
@app.get("/api/cart")
@limiter.limit("100/minute")
async def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's cart"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.get_user_cart(current_user.id)
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cart"
        )

@app.post("/api/cart/items")
@limiter.limit("50/minute")
async def add_to_cart(
    book_id: int,
    quantity: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add item to cart"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.add_item_to_cart(
            current_user.id, book_id, quantity
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )

@app.put("/api/cart/items/{item_id}")
@limiter.limit("50/minute")
async def update_cart_item(
    item_id: int,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.update_cart_item(
            current_user.id, item_id, quantity
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating cart item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )

@app.delete("/api/cart/items/{item_id}")
@limiter.limit("50/minute")
async def remove_from_cart(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.remove_item_from_cart(
            current_user.id, item_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove item from cart"
        )

@app.delete("/api/cart")
@limiter.limit("20/minute")
async def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear user's cart"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.clear_cart(current_user.id)
    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )

@app.get("/api/cart/summary")
@limiter.limit("100/minute")
async def get_cart_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cart summary"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.get_cart_summary(current_user.id)
    except Exception as e:
        logger.error(f"Error getting cart summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart summary"
        )

# User endpoints
@app.get("/api/users/me")
@limiter.limit("100/minute")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    try:
        return {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at
        }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@app.put("/api/users/me")
@limiter.limit("10/minute")
async def update_user_info(
    name: str = None,
    email: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    try:
        user_service = UltraOptimizedUserService(db)
        return await user_service.update_user(
            current_user.id, name=name, email=email
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user information"
        )

# Bookshelf endpoints
@app.get("/api/bookshelves")
@limiter.limit("100/minute")
async def get_user_bookshelves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's bookshelves"""
    try:
        bookshelf_service = UltraOptimizedBookshelfService(db)
        return await bookshelf_service.get_user_bookshelves(current_user.id)
    except Exception as e:
        logger.error(f"Error getting bookshelves: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookshelves"
        )

@app.post("/api/bookshelves")
@limiter.limit("20/minute")
async def create_bookshelf(
    name: str,
    description: str = None,
    is_public: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new bookshelf"""
    try:
        bookshelf_service = UltraOptimizedBookshelfService(db)
        return await bookshelf_service.create_bookshelf(
            current_user.id, name, description, is_public
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating bookshelf: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bookshelf"
        )

@app.post("/api/bookshelves/{bookshelf_id}/books")
@limiter.limit("50/minute")
async def add_book_to_bookshelf(
    bookshelf_id: int,
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add book to bookshelf"""
    try:
        bookshelf_service = UltraOptimizedBookshelfService(db)
        return await bookshelf_service.add_book_to_bookshelf(
            current_user.id, bookshelf_id, book_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding book to bookshelf: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add book to bookshelf"
        )

@app.delete("/api/bookshelves/{bookshelf_id}/books/{book_id}")
@limiter.limit("50/minute")
async def remove_book_from_bookshelf(
    bookshelf_id: int,
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove book from bookshelf"""
    try:
        bookshelf_service = UltraOptimizedBookshelfService(db)
        return await bookshelf_service.remove_book_from_bookshelf(
            current_user.id, bookshelf_id, book_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing book from bookshelf: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove book from bookshelf"
        )

# Search endpoint
@app.get("/api/search")
@limiter.limit("200/minute")
async def search_books(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search books"""
    try:
        book_service = UltraOptimizedBookService(db)
        result = book_service.get_books_ultra_optimized(
            search=q,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error searching books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search books"
        )

# Analytics endpoint
@app.get("/api/analytics/cart")
@limiter.limit("10/minute")
async def get_cart_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cart analytics"""
    try:
        cart_service = UltraOptimizedCartService(db)
        return await cart_service.get_cart_analytics(current_user.id)
    except Exception as e:
        logger.error(f"Error getting cart analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cart analytics"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level="info"
    ) 