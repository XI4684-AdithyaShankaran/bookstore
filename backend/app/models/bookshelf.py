from sqlalchemy import Column, Integer, String, Sequence, Text, DateTime
from datetime import datetime
from .book import Base

class Bookshelf(Base):
    __tablename__ = "bookshelves"

    id = Column(Integer, Sequence("bookshelf_id_seq"), primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    description = Column(Text)
    is_public = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class BookshelfBook(Base):
    __tablename__ = "bookshelf_books"

    id = Column(Integer, Sequence("bookshelf_book_id_seq"), primary_key=True)
    bookshelf_id = Column(Integer)
    book_id = Column(Integer)
    added_at = Column(DateTime, default=datetime.utcnow) 