from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..models.user import User
from ..models.book import Book
import logging
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from ..models.wishlist import WishlistItem

logger = logging.getLogger(__name__)

class WishlistService:
    """Wishlist service for managing user wishlists"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_wishlist(self, user_id: int) -> Dict[str, Any]:
        """Get user's wishlist"""
        try:
            items = self.db.query(WishlistItem).filter(WishlistItem.user_id == user_id).all()
            return {
                "items": [{"book_id": item.book_id, "added_at": item.added_at} for item in items],
                "item_count": len(items)
            }
        except Exception as e:
            logger.error(f"❌ Error getting user wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching wishlist")
    
    async def add_to_wishlist(self, user_id: int, book_id: int) -> Dict[str, Any]:
        """Add item to user's wishlist"""
        try:
            # Check if book exists
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

            # Check if already in wishlist
            existing = self.db.query(WishlistItem).filter(
                WishlistItem.user_id == user_id,
                WishlistItem.book_id == book_id
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Book already in wishlist")

            new_item = WishlistItem(user_id=user_id, book_id=book_id)
            self.db.add(new_item)
            self.db.commit()
            self.db.refresh(new_item)
            return {
                "message": "Item added to wishlist",
                "book_id": book_id,
                "added_at": new_item.added_at
            }
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"❌ Integrity error adding to wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data")
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error adding to wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error adding to wishlist")
    
    async def remove_from_wishlist(self, user_id: int, book_id: int) -> None:
        """Remove item from user's wishlist"""
        try:
            item = self.db.query(WishlistItem).filter(
                WishlistItem.user_id == user_id,
                WishlistItem.book_id == book_id
            ).first()
            if not item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in wishlist")

            self.db.delete(item)
            self.db.commit()
            logger.info(f"Item {book_id} removed from user {user_id} wishlist")
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error removing from wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error removing from wishlist")
    
    async def clear_wishlist(self, user_id: int) -> None:
        """Clear user's wishlist"""
        try:
            self.db.query(WishlistItem).filter(WishlistItem.user_id == user_id).delete()
            self.db.commit()
            logger.info(f"Wishlist cleared for user {user_id}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error clearing wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error clearing wishlist")
    
    async def is_in_wishlist(self, user_id: int, book_id: int) -> bool:
        """Check if book is in user's wishlist"""
        try:
            exists = self.db.query(WishlistItem).filter(
                WishlistItem.user_id == user_id,
                WishlistItem.book_id == book_id
            ).first() is not None
            return exists
        except Exception as e:
            logger.error(f"❌ Error checking wishlist: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error checking wishlist") 