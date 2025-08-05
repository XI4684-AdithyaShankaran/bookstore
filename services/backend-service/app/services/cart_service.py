#!/usr/bin/env python3
"""
Production-Ready Cart Service for Bkmrk'd Bookstore
Industrial standard cart management with optimized performance
"""

import logging
import time
import threading
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy import and_, or_, func, desc, asc
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.user import User
from app.models.book import Book
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.services.book_service import BookService

logger = logging.getLogger(__name__)

class CartService:
    """Cart service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.book_service = BookService(db)
        self._cache = {}
        self._cache_lock = threading.RLock()
        self._last_cleanup = time.time()
        self.CACHE_TTL = 1800  # 30 minutes
        self.MAX_CACHE_SIZE = 500
    
    def _cleanup_cache(self):
        """Cache cleanup"""
        current_time = time.time()
        if current_time - self._last_cleanup > 300:  # Every 5 minutes
            with self._cache_lock:
                expired_keys = [
                    key for key, (_, timestamp) in self._cache.items()
                    if current_time - timestamp > self.CACHE_TTL
                ]
                for key in expired_keys:
                    del self._cache[key]
                self._last_cleanup = current_time
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached value with cleanup"""
        self._cleanup_cache()
        with self._cache_lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.CACHE_TTL:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def _set_cached(self, key: str, value: Any) -> Any:
        """Set cached value with size management"""
        with self._cache_lock:
            if len(self._cache) >= self.MAX_CACHE_SIZE:
                # Remove oldest entries
                oldest_keys = sorted(
                    self._cache.keys(),
                    key=lambda k: self._cache[k][1]
                )[:100]
                for old_key in oldest_keys:
                    del self._cache[old_key]
            
            self._cache[key] = (value, time.time())
        return value
    
    async def get_user_cart(self, user_id: int) -> CartResponse:
        """Get user's cart"""
        try:
            cache_key = f"cart_{user_id}"
            cached_result = self._get_cached(cache_key)
            if cached_result:
                return cached_result
            
            # Query with essential columns
            cart = self.db.query(Cart).options(
                joinedload(Cart.items).joinedload(CartItem.book).load_only(
                    Book.id, Book.title, Book.author, Book.price, Book.cover_image
                )
            ).filter(Cart.user_id == user_id).first()
            
            if not cart:
                # Create new cart
                cart = Cart(user_id=user_id)
                self.db.add(cart)
                self.db.commit()
                self.db.refresh(cart)
            
            # Calculate totals efficiently
            total_items = sum(item.quantity for item in cart.items)
            total_amount = sum(
                item.quantity * item.book.price for item in cart.items
            )
            
            result = CartResponse(
                id=cart.id,
                user_id=cart.user_id,
                items=[
                    {
                        "id": item.id,
                        "book_id": item.book_id,
                        "quantity": item.quantity,
                        "price": float(item.book.price),
                        "book": {
                            "id": item.book.id,
                            "title": item.book.title,
                            "author": item.book.author,
                            "price": float(item.book.price),
                            "cover_image": item.book.cover_image
                        }
                    }
                    for item in cart.items
                ],
                total_items=total_items,
                total_amount=float(total_amount),
                created_at=cart.created_at,
                updated_at=cart.updated_at
            )
            
            return self._set_cached(cache_key, result)
            
        except Exception as e:
            logger.error(f"Error getting user cart: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve cart"
            )
    
    async def add_item_to_cart(
        self, 
        user_id: int, 
        book_id: int, 
        quantity: int = 1
    ) -> CartResponse:
        """Add item to cart with validation and optimization"""
        try:
            # Validate book exists and is available
            book = self.db.query(Book).filter(Book.id == book_id).first()
            if not book:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Book not found"
                )
            
            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0"
                )
            
            # Get or create cart
            cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                cart = Cart(user_id=user_id)
                self.db.add(cart)
                self.db.commit()
                self.db.refresh(cart)
            
            # Check if item already exists
            existing_item = self.db.query(CartItem).filter(
                and_(
                    CartItem.cart_id == cart.id,
                    CartItem.book_id == book_id
                )
            ).first()
            
            if existing_item:
                # Update quantity
                existing_item.quantity += quantity
                self.db.commit()
            else:
                # Create new item
                cart_item = CartItem(
                    cart_id=cart.id,
                    book_id=book_id,
                    quantity=quantity
                )
                self.db.add(cart_item)
                self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            # Return updated cart
            return await self.get_user_cart(user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding item to cart: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add item to cart"
            )
    
    async def update_cart_item(
        self, 
        user_id: int, 
        item_id: int, 
        quantity: int
    ) -> CartResponse:
        """Update cart item quantity with validation"""
        try:
            if quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0"
                )
            
            # Get cart item
            cart_item = self.db.query(CartItem).join(Cart).filter(
                and_(
                    CartItem.id == item_id,
                    Cart.user_id == user_id
                )
            ).first()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
            
            # Update quantity
            cart_item.quantity = quantity
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            # Return updated cart
            return await self.get_user_cart(user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update cart item"
            )
    
    async def remove_item_from_cart(
        self, 
        user_id: int, 
        item_id: int
    ) -> CartResponse:
        """Remove item from cart with validation"""
        try:
            # Get cart item
            cart_item = self.db.query(CartItem).join(Cart).filter(
                and_(
                    CartItem.id == item_id,
                    Cart.user_id == user_id
                )
            ).first()
            
            if not cart_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cart item not found"
                )
            
            # Remove item
            self.db.delete(cart_item)
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            # Return updated cart
            return await self.get_user_cart(user_id)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing cart item: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove cart item"
            )
    
    async def clear_cart(self, user_id: int) -> CartResponse:
        """Clear all items from cart"""
        try:
            # Get cart
            cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
            if not cart:
                return await self.get_user_cart(user_id)
            
            # Remove all items
            self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            self.db.commit()
            
            # Clear cache
            self._clear_user_cache(user_id)
            
            # Return updated cart
            return await self.get_user_cart(user_id)
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear cart"
            )
    
    async def get_cart_summary(self, user_id: int) -> Dict[str, Any]:
        """Get cart summary for quick display"""
        try:
            cache_key = f"cart_summary_{user_id}"
            cached_result = self._get_cached(cache_key)
            if cached_result:
                return cached_result
            
            # Summary query
            result = self.db.query(
                func.count(CartItem.id).label('total_items'),
                func.sum(CartItem.quantity * Book.price).label('total_amount')
            ).join(Cart).join(Book).filter(
                Cart.user_id == user_id
            ).first()
            
            summary = {
                "total_items": result.total_items or 0,
                "total_amount": float(result.total_amount or 0),
                "item_count": result.total_items or 0
            }
            
            return self._set_cached(cache_key, summary)
            
        except Exception as e:
            logger.error(f"Error getting cart summary: {e}")
            return {"total_items": 0, "total_amount": 0.0, "item_count": 0}
    
    async def apply_discount(
        self, 
        user_id: int, 
        discount_code: str
    ) -> Dict[str, Any]:
        """Apply discount to cart with validation"""
        try:
            # Get cart
            cart = await self.get_user_cart(user_id)
            
            if not cart.items:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cart is empty"
                )
            
            # Validate discount code (simplified)
            discount_amount = 0.0
            if discount_code.upper() == "WELCOME10":
                discount_amount = cart.total_amount * 0.10
            elif discount_code.upper() == "SAVE20":
                discount_amount = cart.total_amount * 0.20
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid discount code"
                )
            
            return {
                "original_total": cart.total_amount,
                "discount_amount": discount_amount,
                "final_total": cart.total_amount - discount_amount,
                "discount_code": discount_code
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying discount: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to apply discount"
            )
    
    def _clear_user_cache(self, user_id: int):
        """Clear user-specific cache entries"""
        with self._cache_lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if f"cart_{user_id}" in key or f"cart_summary_{user_id}" in key
            ]
            for key in keys_to_remove:
                del self._cache[key]
    
    async def get_cart_analytics(self, user_id: int) -> Dict[str, Any]:
        """Get cart analytics for insights"""
        try:
            cart = await self.get_user_cart(user_id)
            
            if not cart.items:
                return {
                    "total_items": 0,
                    "total_value": 0.0,
                    "average_item_price": 0.0,
                    "most_expensive_item": None,
                    "genre_distribution": {}
                }
            
            # Calculate analytics
            total_value = cart.total_amount
            average_price = total_value / cart.total_items if cart.total_items > 0 else 0
            
            # Find most expensive item
            most_expensive = max(cart.items, key=lambda x: x["price"]) if cart.items else None
            
            # Genre distribution
            genre_distribution = {}
            for item in cart.items:
                genre = item["book"].get("genre", "Unknown")
                genre_distribution[genre] = genre_distribution.get(genre, 0) + item["quantity"]
            
            return {
                "total_items": cart.total_items,
                "total_value": total_value,
                "average_item_price": average_price,
                "most_expensive_item": most_expensive,
                "genre_distribution": genre_distribution
            }
            
        except Exception as e:
            logger.error(f"Error getting cart analytics: {e}")
            return {
                "total_items": 0,
                "total_value": 0.0,
                "average_item_price": 0.0,
                "most_expensive_item": None,
                "genre_distribution": {}
            } 