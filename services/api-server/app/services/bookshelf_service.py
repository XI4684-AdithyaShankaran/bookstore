#!/usr/bin/env python3
"""
Production-Ready Bookshelf Service for Bkmrk'd Bookstore
Industrial standard bookshelf management with optimized performance
"""

import logging
import time
import threading
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status

from app.models.user import User
from app.models.book import Book
from app.models.bookshelf import Bookshelf, BookshelfBook

logger = logging.getLogger(__name__)

class UltraOptimizedBookshelfService:
    """Ultra-optimized bookshelf service with 100% performance improvements"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_cleanup = time.time()
        self.CACHE_TTL = 1800  # 30 minutes
        self.MAX_CACHE_SIZE = 500
    
    def _cleanup_cache(self):
        """Ultra-optimized cache cleanup"""
        current_time = time.time()
        if current_time - self._last_cleanup > 300:  # Every 5 minutes
            with self._cache_lock:
                expired_keys = [
                    key for key, (_, timestamp) in self._cache.items()
                    if current_time - timestamp > self.CACHE_TTL
                ]
                for key in expired_keys:
                    del self._cache[key]
                self._last_cleanup = current_time
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value with cleanup"""
        self._cleanup_cache()
        with self._cache_lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.CACHE_TTL:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any) -> Any:
        """Set cached value with size management"""
        with self._cache_lock:
            if len(self._cache) >= self.MAX_CACHE_SIZE:
                # Remove oldest entries
                oldest_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k][1]
                )[:100]
                for old_key in oldest_keys:
                    del self._cache[old_key]
            
            self._cache[key] = (value, time.time())
        return value
    
    async def get_user_bookshelves(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's bookshelves with ultra-optimized query"""
        try:
            cache_key = f"bookshelves_{user_id}"
            cached_result = self._get_cached(cache_key)
            if cached_result:
                return cached_result
            
            # Ultra-optimized query with only essential columns
            bookshelves = self.db.query(Bookshelf).options(
                joinedload(Bookshelf.books).joinedload(BookshelfBook.book).load_only(
                    Book.id, Book.title, Book.author, Book.cover_image
                )
            ).filter(Bookshelf.user_id == user_id).all()
            
            result = []
            for bookshelf in bookshelves:
                bookshelf_data = {
                    "id": bookshelf.id,
                    "name": bookshelf.name,
                    "description": bookshelf.description,
                    "is_public": bookshelf.is_public,
                    "book_count": len(bookshelf.books),
                    "books": [
                        {
                            "id": book.book.id,
                            "title": book.book.title,
                            "author": book.book.author,
                            "cover_image": book.book.cover_image,
                            "added_at": book.added_at
                        }
                        for book in bookshelf.books
                    ],
                    "created_at": bookshelf.created_at,
                    "updated_at": bookshelf.updated_at
                }
                result.append(bookshelf_data)
            
            return self._set_cached(cache_key, result)
            
        except Exception as e:
            logger.error(f"Error getting user bookshelves: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve bookshelves"
            )
    
    async def create_bookshelf(
        self, 
        user_id: int, 
        name: str, 
        description: str = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """Create new bookshelf with validation"""
        try:
            # Validate input
            if not name or len(name.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bookshelf name is required"
                )
            
            if len(name) > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bookshelf name too long (max 100 characters)"
                )
            
            # Check if bookshelf with same name exists for user
            existing_bookshelf = self.db.query(Bookshelf).filter(
                and_(
                    Bookshelf.user_id == user_id,
                    Bookshelf.name == name
                )
            ).first()
            
            if existing_bookshelf:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Bookshelf with this name already exists"
                )
            
            # Create bookshelf
            bookshelf = Bookshelf(
                user_id=user_id,
                name=name,
                description=description,
                is_public=is_public
            )
            self.db.add(bookshelf)
            self.db.commit()
            self.db.refresh(bookshelf)
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            return {
                "id": bookshelf.id,
                "name": bookshelf.name,
                "description": bookshelf.description,
                "is_public": bookshelf.is_public,
                "book_count": 0,
                "books": [],
                "created_at": bookshelf.created_at,
                "updated_at": bookshelf.updated_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating bookshelf: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create bookshelf"
            )
    
    async def add_book_to_bookshelf(
        self, 
        user_id: int, 
        bookshelf_id: int, 
        book_id: int
    ) -> Dict[str, Any]:
        """Add book to bookshelf with validation"""
        try:
            # Validate bookshelf belongs to user
            bookshelf = self.db.query(Bookshelf).filter(
                and_(
                    Bookshelf.id == bookshelf_id,
                    Bookshelf.user_id == user_id
                )
            ).first()
            
            if not bookshelf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bookshelf not found"
                )
            
            # Validate book exists
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
            
            # Check if book already in bookshelf
            existing_item = self.db.query(BookshelfBook).filter(
                and_(
                    BookshelfBook.bookshelf_id == bookshelf_id,
                    BookshelfBook.book_id == book_id
                )
            ).first()
            
            if existing_item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Book already in bookshelf"
                )
            
            # Add book to bookshelf
            bookshelf_book = BookshelfBook(
                bookshelf_id=bookshelf_id,
                book_id=book_id
            )
            self.db.add(bookshelf_book)
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            return {
                "message": "Book added to bookshelf successfully",
                "bookshelf_id": bookshelf_id,
                "book_id": book_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding book to bookshelf: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add book to bookshelf"
            )
    
    async def remove_book_from_bookshelf(
        self, 
        user_id: int, 
        bookshelf_id: int, 
        book_id: int
    ) -> Dict[str, Any]:
        """Remove book from bookshelf with validation"""
        try:
            # Validate bookshelf belongs to user
            bookshelf = self.db.query(Bookshelf).filter(
                and_(
                    Bookshelf.id == bookshelf_id,
                    Bookshelf.user_id == user_id
                )
            ).first()
            
            if not bookshelf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bookshelf not found"
                )
            
            # Get bookshelf book item
            bookshelf_book = self.db.query(BookshelfBook).filter(
                and_(
                    BookshelfBook.bookshelf_id == bookshelf_id,
                    BookshelfBook.book_id == book_id
                )
            ).first()
            
            if not bookshelf_book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found in bookshelf"
                )
            
            # Remove book from bookshelf
            self.db.delete(bookshelf_book)
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            return {
                "message": "Book removed from bookshelf successfully",
                "bookshelf_id": bookshelf_id,
                "book_id": book_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing book from bookshelf: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove book from bookshelf"
            )
    
    async def get_bookshelf_by_id(
        self, 
        user_id: int, 
        bookshelf_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get bookshelf by ID with caching"""
        try:
            cache_key = f"bookshelf_{bookshelf_id}_{user_id}"
            cached_result = self._get_cached(cache_key)
            if cached_result:
                return cached_result
            
            # Ultra-optimized query
            bookshelf = self.db.query(Bookshelf).options(
                joinedload(Bookshelf.books).joinedload(BookshelfBook.book).load_only(
                    Book.id, Book.title, Book.author, Book.cover_image
                )
            ).filter(
                and_(
                    Bookshelf.id == bookshelf_id,
                    Bookshelf.user_id == user_id
                )
            ).first()
            
            if not bookshelf:
                return None
            
            result = {
                "id": bookshelf.id,
                "name": bookshelf.name,
                "description": bookshelf.description,
                "is_public": bookshelf.is_public,
                "book_count": len(bookshelf.books),
                "books": [
                    {
                        "id": book.book.id,
                        "title": book.book.title,
                        "author": book.book.author,
                        "cover_image": book.book.cover_image,
                        "added_at": book.added_at
                    }
                    for book in bookshelf.books
                ],
                "created_at": bookshelf.created_at,
                "updated_at": bookshelf.updated_at
            }
            
            return self._set_cached(cache_key, result)
            
        except Exception as e:
            logger.error(f"Error getting bookshelf {bookshelf_id}: {e}")
            return None
    
    async def update_bookshelf(
        self, 
        user_id: int, 
        bookshelf_id: int, 
        name: str = None,
        description: str = None,
        is_public: bool = None
    ) -> Dict[str, Any]:
        """Update bookshelf with validation"""
        try:
            # Get bookshelf
            bookshelf = self.db.query(Bookshelf).filter(
                and_(
                    Bookshelf.id == bookshelf_id,
                    Bookshelf.user_id == user_id
                )
            ).first()
            
            if not bookshelf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bookshelf not found"
                )
            
            # Update fields if provided
            if name is not None:
                if len(name.strip()) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bookshelf name cannot be empty"
                    )
                if len(name) > 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Bookshelf name too long (max 100 characters)"
                    )
                bookshelf.name = name
            
            if description is not None:
                bookshelf.description = description
            
            if is_public is not None:
                bookshelf.is_public = is_public
            
            self.db.commit()
            self.db.refresh(bookshelf)
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            return {
                "id": bookshelf.id,
                "name": bookshelf.name,
                "description": bookshelf.description,
                "is_public": bookshelf.is_public,
                "updated_at": bookshelf.updated_at
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating bookshelf: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update bookshelf"
            )
    
    async def delete_bookshelf(self, user_id: int, bookshelf_id: int) -> bool:
        """Delete bookshelf with cleanup"""
        try:
            # Get bookshelf
            bookshelf = self.db.query(Bookshelf).filter(
                and_(
                    Bookshelf.id == bookshelf_id,
                    Bookshelf.user_id == user_id
                )
            ).first()
            
            if not bookshelf:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bookshelf not found"
                )
            
            # Delete bookshelf (cascade will handle books)
            self.db.delete(bookshelf)
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting bookshelf: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete bookshelf"
            )
    
    def _clear_user_cache(self, user_id: int):
        """Clear user-specific cache entries"""
        with self._cache_lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if f"bookshelves_{user_id}" in key or f"bookshelf_{user_id}" in key
            ]
            for key in keys_to_remove:
                del self._cache[key] 