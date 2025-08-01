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
    books = relationship("BookshelfBook", back_populates="bookshelf")

class BookshelfBook(Base):
    __tablename__ = "bookshelf_books"
    
    id = Column(Integer, primary_key=True, index=True)
    bookshelf_id = Column(Integer, ForeignKey("bookshelves.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bookshelf = relationship("Bookshelf", back_populates="books")
    book = relationship("Book") 