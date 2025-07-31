from sqlalchemy import Column, Integer, String, Sequence, Text, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, Sequence("book_id_seq"), primary_key=True)
    title = Column(String, index=True)
    author = Column(String, index=True)
    year = Column(Integer)
    genre = Column(String)
    description = Column(Text)
    isbn = Column(String, unique=True, index=True)
    rating = Column(Float)
    pages = Column(Integer)
    language = Column(String)
    publisher = Column(String)
    cover_image = Column(String)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 