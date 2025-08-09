#!/usr/bin/env python3
"""
Comprehensive Recommendation Service for Bkmrk'd Bookstore
Provides AI-powered recommendations for all user interactions
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from fastapi import HTTPException, status

from app.models.book import Book
from app.models.user import User
from app.models.bookshelf import Bookshelf, BookshelfBook
from app.models.cart import Cart
from app.models.wishlist import WishlistItem
from app.models.order import Order, OrderItem

logger = logging.getLogger(__name__)

class RecommendationService:
    """Comprehensive recommendation service with AI integration"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service_url = "http://ai-ml-service:8003"
        self.cache = {}
    
    async def get_user_recommendations(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized recommendations for user"""
        try:
            # Get user preferences and history
            user_data = await self._get_user_data(user_id)
            
            # Call AI service for recommendations
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ai_service_url}/recommendations",
                    json={
                        "user_id": user_id,
                        "user_preferences": user_data["preferences"],
                        "limit": limit
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    ai_recommendations = response.json()
                    return await self._enhance_recommendations(ai_recommendations["recommendations"], user_data)
                else:
                    logger.warning(f"AI service unavailable, falling back to rule-based recommendations")
                    return await self._get_rule_based_recommendations(user_data, limit)
                    
        except Exception as e:
            logger.error(f"❌ Error getting user recommendations: {e}")
            return await self._get_rule_based_recommendations(user_data, limit)
    
    async def get_wishlist_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on user's wishlist"""
        try:
            # Get user's wishlist
            wishlist_items = self.db.query(WishlistItem).filter(WishlistItem.user_id == user_id).all()
            
            if not wishlist_items:
                return await self._get_popular_books(limit)
            
            # Get genres from wishlist
            wishlist_book_ids = [item.book_id for item in wishlist_items]
            wishlist_books = self.db.query(Book).filter(Book.id.in_(wishlist_book_ids)).all()
            
            genres = list(set([book.genre for book in wishlist_books if book.genre]))
            
            # Get similar books by genre and rating
            similar_books = self.db.query(Book).filter(
                and_(
                    Book.genre.in_(genres),
                    ~Book.id.in_(wishlist_book_ids),
                    Book.rating >= 4.0
                )
            ).order_by(desc(Book.rating)).limit(limit).all()
            
            return [self._book_to_dict(book) for book in similar_books]
            
        except Exception as e:
            logger.error(f"❌ Error getting wishlist recommendations: {e}")
            return await self._get_popular_books(limit)
    
    async def get_bookshelf_recommendations(self, user_id: int, bookshelf_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations for a specific bookshelf"""
        try:
            # Get bookshelf details
            bookshelf = self.db.query(Bookshelf).filter(
                and_(Bookshelf.id == bookshelf_id, Bookshelf.user_id == user_id)
            ).first()
            
            if not bookshelf:
                raise HTTPException(status_code=404, detail="Bookshelf not found")
            
            # Get books in the bookshelf
            bookshelf_books = self.db.query(BookshelfBook).filter(BookshelfBook.bookshelf_id == bookshelf_id).all()
            
            if not bookshelf_books:
                return await self._get_popular_books(limit)
            
            book_ids = [bb.book_id for bb in bookshelf_books]
            books = self.db.query(Book).filter(Book.id.in_(book_ids)).all()
            
            # Get similar books by genre and author
            genres = list(set([book.genre for book in books if book.genre]))
            authors = list(set([book.author for book in books if book.author]))
            
            similar_books = self.db.query(Book).filter(
                and_(
                    or_(
                        Book.genre.in_(genres),
                        Book.author.in_(authors)
                    ),
                    ~Book.id.in_(book_ids),
                    Book.rating >= 3.5
                )
            ).order_by(desc(Book.rating)).limit(limit).all()
            
            return [self._book_to_dict(book) for book in similar_books]
            
        except Exception as e:
            logger.error(f"❌ Error getting bookshelf recommendations: {e}")
            return await self._get_popular_books(limit)
    
    async def get_cart_recommendations(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on user's cart"""
        try:
            # Get cart items
            cart_items = self.db.query(Cart).filter(Cart.user_id == user_id).all()
            
            if not cart_items:
                return await self._get_popular_books(limit)
            
            cart_book_ids = [item.book_id for item in cart_items]
            cart_books = self.db.query(Book).filter(Book.id.in_(cart_book_ids)).all()
            
            # Get complementary books (different genres)
            cart_genres = list(set([book.genre for book in cart_books if book.genre]))
            
            complementary_books = self.db.query(Book).filter(
                and_(
                    ~Book.genre.in_(cart_genres),
                    ~Book.id.in_(cart_book_ids),
                    Book.rating >= 4.0
                )
            ).order_by(desc(Book.rating)).limit(limit).all()
            
            return [self._book_to_dict(book) for book in complementary_books]
            
        except Exception as e:
            logger.error(f"❌ Error getting cart recommendations: {e}")
            return await self._get_popular_books(limit)
    
    async def get_book_recommendations(self, book_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on a specific book"""
        try:
            # Get book details
            book = self.db.query(Book).filter(Book.id == book_id).first()
            
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            
            # Get similar books by genre, author, and rating
            similar_books = self.db.query(Book).filter(
                and_(
                    or_(
                        Book.genre == book.genre,
                        Book.author == book.author
                    ),
                    Book.id != book_id,
                    Book.rating >= book.rating - 0.5
                )
            ).order_by(desc(Book.rating)).limit(limit).all()
            
            return [self._book_to_dict(b) for b in similar_books]
            
        except Exception as e:
            logger.error(f"❌ Error getting book recommendations: {e}")
            return await self._get_popular_books(limit)
    
    async def get_trending_recommendations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending book recommendations"""
        try:
            # Get books with high ratings and many reviews
            trending_books = self.db.query(Book).filter(
                and_(
                    Book.rating >= 4.0,
                    Book.ratings_count >= 1000
                )
            ).order_by(desc(Book.ratings_count)).limit(limit).all()
            
            return [self._book_to_dict(book) for book in trending_books]
            
        except Exception as e:
            logger.error(f"❌ Error getting trending recommendations: {e}")
            return []
    
    async def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user data for recommendations"""
        try:
            # Get user's reading history
            orders = self.db.query(Order).filter(Order.user_id == user_id).all()
            order_book_ids = []
            
            for order in orders:
                order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                order_book_ids.extend([item.book_id for item in order_items])
            
            # Get user's wishlist
            wishlist_items = self.db.query(WishlistItem).filter(WishlistItem.user_id == user_id).all()
            wishlist_book_ids = [item.book_id for item in wishlist_items]
            
            # Get user's bookshelves
            bookshelves = self.db.query(Bookshelf).filter(Bookshelf.user_id == user_id).all()
            bookshelf_book_ids = []
            
            for bookshelf in bookshelves:
                bookshelf_books = self.db.query(BookshelfBook).filter(BookshelfBook.bookshelf_id == bookshelf.id).all()
                bookshelf_book_ids.extend([bb.book_id for bb in bookshelf_books])
            
            # Get all user's books
            all_book_ids = list(set(order_book_ids + wishlist_book_ids + bookshelf_book_ids))
            user_books = self.db.query(Book).filter(Book.id.in_(all_book_ids)).all()
            
            # Extract preferences
            genres = list(set([book.genre for book in user_books if book.genre]))
            authors = list(set([book.author for book in user_books if book.author]))
            
            return {
                "user_id": user_id,
                "preferences": {
                    "genres": genres,
                    "authors": authors,
                    "avg_rating": sum([book.rating for book in user_books]) / len(user_books) if user_books else 0,
                    "total_books": len(user_books)
                },
                "history": {
                    "purchased": order_book_ids,
                    "wishlisted": wishlist_book_ids,
                    "bookshelved": bookshelf_book_ids
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user data: {e}")
            return {"user_id": user_id, "preferences": {}, "history": {}}
    
    async def _enhance_recommendations(self, ai_recommendations: List[Dict], user_data: Dict) -> List[Dict[str, Any]]:
        """Enhance AI recommendations with database data"""
        try:
            enhanced_recommendations = []
            
            for rec in ai_recommendations:
                # Try to find the book in our database
                book = self.db.query(Book).filter(
                    Book.title.ilike(f"%{rec['title']}%")
                ).first()
                
                if book:
                    enhanced_recommendations.append(self._book_to_dict(book))
                else:
                    # Add AI recommendation as fallback
                    enhanced_recommendations.append({
                        "id": None,
                        "title": rec["title"],
                        "author": rec["author"],
                        "genre": rec["genre"],
                        "rating": rec.get("confidence", 0.0),
                        "reasoning": rec.get("reasoning", ""),
                        "is_ai_generated": True
                    })
            
            return enhanced_recommendations
            
        except Exception as e:
            logger.error(f"❌ Error enhancing recommendations: {e}")
            return ai_recommendations
    
    async def _get_rule_based_recommendations(self, user_data: Dict, limit: int) -> List[Dict[str, Any]]:
        """Get rule-based recommendations when AI is unavailable"""
        try:
            preferences = user_data.get("preferences", {})
            genres = preferences.get("genres", [])
            
            if genres:
                # Get books by user's preferred genres
                books = self.db.query(Book).filter(
                    and_(
                        Book.genre.in_(genres),
                        Book.rating >= 4.0
                    )
                ).order_by(desc(Book.rating)).limit(limit).all()
            else:
                # Get popular books
                books = await self._get_popular_books(limit)
            
            return [self._book_to_dict(book) for book in books]
            
        except Exception as e:
            logger.error(f"❌ Error getting rule-based recommendations: {e}")
            return await self._get_popular_books(limit)
    
    async def _get_popular_books(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular books as fallback"""
        try:
            books = self.db.query(Book).filter(
                Book.rating >= 4.0
            ).order_by(desc(Book.ratings_count)).limit(limit).all()
            
            return [self._book_to_dict(book) for book in books]
            
        except Exception as e:
            logger.error(f"❌ Error getting popular books: {e}")
            return []
    
    def _book_to_dict(self, book: Book) -> Dict[str, Any]:
        """Convert book model to dictionary"""
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "description": book.description,
            "rating": book.rating,
            "price": book.price,
            "cover_image": book.cover_image,
            "isbn": book.isbn,
            "pages": book.pages,
            "language": book.language,
            "publisher": book.publisher,
            "year": book.year,
            "ratings_count": book.ratings_count,
            "text_reviews_count": book.text_reviews_count
        } 