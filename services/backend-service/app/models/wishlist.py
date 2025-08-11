from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class WishlistItem(Base):
    __tablename__ = "wishlist"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"), primary_key=True)

    user = relationship("User", back_populates="wishlist_items")
    book = relationship("Book") 