#!/usr/bin/env python3
"""
Book Service for AI Service
Handles database operations for book data
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

class BookService:
    """Service for book data operations"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_books_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get books data from database"""
        try:
            query = text("""
                SELECT id, title, author, description, genre, rating, price, 
                       publication_date, isbn, language, pages, publisher
                FROM books 
                ORDER BY rating DESC 
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {"limit": limit})
            books = []
            
            for row in result:
                books.append({
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "description": row.description,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0,
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "isbn": row.isbn,
                    "language": row.language,
                    "pages": row.pages,
                    "publisher": row.publisher
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error fetching books data: {e}")
            return []
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get specific book by ID"""
        try:
            query = text("""
                SELECT id, title, author, description, genre, rating, price, 
                       publication_date, isbn, language, pages, publisher
                FROM books 
                WHERE id = :book_id
            """)
            
            result = self.db.execute(query, {"book_id": book_id})
            row = result.fetchone()
            
            if row:
                return {
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "description": row.description,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0,
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "isbn": row.isbn,
                    "language": row.language,
                    "pages": row.pages,
                    "publisher": row.publisher
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching book {book_id}: {e}")
            return None
    
    def search_books(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search books by title, author, or description"""
        try:
            search_query = text("""
                SELECT id, title, author, description, genre, rating, price
                FROM books 
                WHERE title ILIKE :search_term 
                   OR author ILIKE :search_term 
                   OR description ILIKE :search_term
                ORDER BY rating DESC 
                LIMIT :limit
            """)
            
            search_term = f"%{query}%"
            result = self.db.execute(search_query, {"search_term": search_term, "limit": limit})
            
            books = []
            for row in result:
                books.append({
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "description": row.description,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error searching books: {e}")
            return [] 