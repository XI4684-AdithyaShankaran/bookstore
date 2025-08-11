from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Bookshelf(Base):
    __tablename__ = "bookshelves"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="bookshelves")
    books = relationship("Book", secondary="bookshelf_books", back_populates="bookshelves")

class BookshelfBook(Base):
    __tablename__ = "bookshelf_books"
    
    bookshelf_id = Column(Integer, ForeignKey("bookshelves.id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True) 