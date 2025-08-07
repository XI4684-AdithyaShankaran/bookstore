"""
Rating Service for Bkmrk'd Bookstore
Handles all rating-related operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.models import Rating, Book, User


class RatingService:
    """Service for managing book ratings and reviews"""
    
    def get_ratings(self, db: Session, skip: int = 0, limit: int = 100) -> List[Rating]:
        """Get all ratings with pagination"""
        return db.query(Rating).offset(skip).limit(limit).all()
    
    def get_rating_by_id(self, db: Session, rating_id: int) -> Optional[Rating]:
        """Get a specific rating by ID"""
        return db.query(Rating).filter(Rating.id == rating_id).first()
    
    def get_ratings_by_user(self, db: Session, user_id: int) -> List[Rating]:
        """Get all ratings by a specific user"""
        return db.query(Rating).filter(Rating.user_id == user_id).all()
    
    def get_ratings_by_book(self, db: Session, book_id: int) -> List[Rating]:
        """Get all ratings for a specific book"""
        return db.query(Rating).filter(Rating.book_id == book_id).all()
    
    def get_user_rating_for_book(self, db: Session, user_id: int, book_id: int) -> Optional[Rating]:
        """Get a user's rating for a specific book"""
        return db.query(Rating).filter(
            Rating.user_id == user_id,
            Rating.book_id == book_id
        ).first()
    
    def create_rating(self, db: Session, user_id: int, book_id: int, rating: float, review: str = None) -> Rating:
        """Create a new rating"""
        # Check if user already rated this book
        existing_rating = self.get_user_rating_for_book(db, user_id, book_id)
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review = review
            db.commit()
            db.refresh(existing_rating)
            return existing_rating
        
        # Create new rating
        db_rating = Rating(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            review=review
        )
        db.add(db_rating)
        db.commit()
        db.refresh(db_rating)
        
        # Update book's average rating
        self._update_book_average_rating(db, book_id)
        
        return db_rating
    
    def update_rating(self, db: Session, rating_id: int, rating: float = None, review: str = None) -> Optional[Rating]:
        """Update an existing rating"""
        db_rating = self.get_rating_by_id(db, rating_id)
        if not db_rating:
            return None
        
        if rating is not None:
            db_rating.rating = rating
        if review is not None:
            db_rating.review = review
        
        db.commit()
        db.refresh(db_rating)
        
        # Update book's average rating
        self._update_book_average_rating(db, db_rating.book_id)
        
        return db_rating
    
    def delete_rating(self, db: Session, rating_id: int) -> bool:
        """Delete a rating"""
        db_rating = self.get_rating_by_id(db, rating_id)
        if not db_rating:
            return False
        
        book_id = db_rating.book_id
        db.delete(db_rating)
        db.commit()
        
        # Update book's average rating
        self._update_book_average_rating(db, book_id)
        
        return True
    
    def get_book_rating_stats(self, db: Session, book_id: int) -> dict:
        """Get rating statistics for a book"""
        ratings = db.query(Rating).filter(Rating.book_id == book_id).all()
        
        if not ratings:
            return {
                "average_rating": 0.0,
                "total_ratings": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }
        
        total_ratings = len(ratings)
        average_rating = sum(r.rating for r in ratings) / total_ratings
        
        # Rating distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for rating in ratings:
            rounded_rating = round(rating.rating)
            if 1 <= rounded_rating <= 5:
                distribution[rounded_rating] += 1
        
        return {
            "average_rating": round(average_rating, 2),
            "total_ratings": total_ratings,
            "rating_distribution": distribution
        }
    
    def get_top_rated_books(self, db: Session, limit: int = 10) -> List[dict]:
        """Get top rated books"""
        # Get books with their average ratings
        results = db.query(
            Book,
            func.avg(Rating.rating).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        ).join(Rating).group_by(Book.id).having(
            func.count(Rating.id) >= 5  # Minimum 5 ratings
        ).order_by(desc('avg_rating')).limit(limit).all()
        
        return [
            {
                "book": result[0],
                "average_rating": round(float(result[1]), 2),
                "rating_count": result[2]
            }
            for result in results
        ]
    
    def get_recent_ratings(self, db: Session, limit: int = 20) -> List[Rating]:
        """Get most recent ratings"""
        return db.query(Rating).order_by(desc(Rating.created_at)).limit(limit).all()
    
    def _update_book_average_rating(self, db: Session, book_id: int):
        """Update a book's average rating"""
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return
        
        ratings = db.query(Rating).filter(Rating.book_id == book_id).all()
        if ratings:
            average_rating = sum(r.rating for r in ratings) / len(ratings)
            book.rating = round(average_rating, 1)
        else:
            book.rating = 0.0
        
        db.commit()