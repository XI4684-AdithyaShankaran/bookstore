from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)  # Added to match migration
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)  # Changed from name to full_name to match migration
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)  # Added to match migration
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships - updated to match actual schema
    cart_items = relationship("CartItem", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    bookshelves = relationship("Bookshelf", back_populates="user")
    wishlist_items = relationship("WishlistItem", back_populates="user", cascade="all, delete-orphan") 