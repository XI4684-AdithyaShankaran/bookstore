from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from ..models.book import Book
from ..schemas.book import BookCreate

class BookService:
    def __init__(self, db: Session):
        self.db = db

    def get_books(self, skip: int = 0, limit: int = 100, search: Optional[str] = None, genre: Optional[str] = None) -> Dict[str, Any]:
        query = self.db.query(Book)
        
        if search:
            query = query.filter(
                or_(
                    Book.title.ilike(f"%{search}%"),
                    Book.author.ilike(f"%{search}%"),
                    Book.description.ilike(f"%{search}%")
                )
            )
        
        if genre:
            query = query.filter(Book.genre == genre)
        
        total = query.count()
        books = query.offset(skip).limit(limit).all()
        
        current_page = (skip // limit) + 1
        has_more = (skip + limit) < total
        
        return {
            "books": books,
            "total": total,
            "page": current_page,
            "limit": limit,
            "hasMore": has_more
        }

    def get_book_by_id(self, book_id: int) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def create_book(self, book_data: BookCreate) -> Book:
        db_book = Book(**book_data.dict())
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    def get_books_by_genre(self, genre: str, limit: int = 20) -> List[Book]:
        return self.db.query(Book).filter(Book.genre == genre).limit(limit).all()

    def get_featured_books(self, limit: int = 6) -> List[Book]:
        return self.db.query(Book).order_by(Book.rating.desc()).limit(limit).all() 