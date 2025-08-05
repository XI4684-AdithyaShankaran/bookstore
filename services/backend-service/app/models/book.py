from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    author = Column(String, nullable=False, index=True)
    genre = Column(String, nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    cover_image = Column(String)
    isbn = Column(String, unique=True, index=True)
    published_date = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 