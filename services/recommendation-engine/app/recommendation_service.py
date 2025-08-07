#!/usr/bin/env python3
"""
Recommendation Engine Microservice for Bkmrk'd
Industrial-grade recommendation system with AI integration
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
import redis
import os

logger = logging.getLogger(__name__)

class RecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    book_id: Optional[int] = None
    context: Optional[str] = None
    limit: int = 10
    strategy: str = "hybrid"  # hybrid, collaborative, content_based, trending

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    confidence_score: float

class RecommendationEngine:
    """Industrial-grade recommendation engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8001")
        self.cache_client = None
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize Redis cache connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.cache_client = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"Cache initialization failed: {e}")
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get recommendations using specified strategy"""
        try:
            cache_key = f"recommendations:{request.strategy}:{request.user_id}:{request.book_id}:{request.limit}"
            
            # Try cache first
            if self.cache_client:
                cached = await self.cache_client.get(cache_key)
                if cached:
                    return RecommendationResponse(**cached)
            
            # Generate recommendations based on strategy
            if request.strategy == "hybrid":
                recommendations = await self._hybrid_recommendations(request)
            elif request.strategy == "collaborative":
                recommendations = await self._collaborative_recommendations(request)
            elif request.strategy == "content_based":
                recommendations = await self._content_based_recommendations(request)
            elif request.strategy == "trending":
                recommendations = await self._trending_recommendations(request)
            else:
                raise HTTPException(status_code=400, detail="Invalid strategy")
            
            # Enhance with ML service
            enhanced_recommendations = await self._enhance_with_ml(recommendations, request)
            
            response = RecommendationResponse(
                recommendations=enhanced_recommendations,
                metadata={
                    "strategy": request.strategy,
                    "user_id": request.user_id,
                    "book_id": request.book_id,
                    "count": len(enhanced_recommendations)
                },
                confidence_score=0.85
            )
            
            # Cache response
            if self.cache_client:
                await self.cache_client.setex(cache_key, 900, response.dict())
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generating recommendations: {e}")
            raise HTTPException(status_code=500, detail="Recommendation generation failed")
    
    async def _hybrid_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Hybrid recommendation combining multiple strategies"""
        recommendations = []
        
        if request.user_id:
            # Get user-based recommendations
            user_recs = await self._collaborative_recommendations(request)
            recommendations.extend(user_recs[:5])
        
        if request.book_id:
            # Get content-based recommendations
            content_recs = await self._content_based_recommendations(request)
            recommendations.extend(content_recs[:3])
        
        # Add trending recommendations
        trending_recs = await self._trending_recommendations(request)
        recommendations.extend(trending_recs[:2])
        
        return recommendations[:request.limit]
    
    async def _collaborative_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendations"""
        try:
            # Get similar users based on reading history
            similar_users = await self._find_similar_users(request.user_id)
            
            # Get books liked by similar users
            recommendations = []
            for user_id in similar_users:
                user_books = await self._get_user_preferred_books(user_id)
                recommendations.extend(user_books)
            
            return self._deduplicate_and_rank(recommendations, request.limit)
            
        except Exception as e:
            logger.error(f"❌ Error in collaborative recommendations: {e}")
            return []
    
    async def _content_based_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Content-based filtering recommendations"""
        try:
            if request.book_id:
                # Get similar books based on features
                similar_books = await self._find_similar_books(request.book_id)
                return similar_books[:request.limit]
            elif request.user_id:
                # Get books similar to user's preferences
                user_preferences = await self._get_user_preferences(request.user_id)
                similar_books = await self._find_books_by_preferences(user_preferences)
                return similar_books[:request.limit]
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error in content-based recommendations: {e}")
            return []
    
    async def _trending_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Trending/popular books recommendations"""
        try:
            # Get trending books based on ratings and popularity
            trending_books = self.db.query(Book).filter(
                and_(
                    Book.rating >= 4.0,
                    Book.ratings_count >= 1000
                )
            ).order_by(desc(Book.ratings_count)).limit(request.limit).all()
            
            return [self._book_to_dict(book) for book in trending_books]
            
        except Exception as e:
            logger.error(f"❌ Error in trending recommendations: {e}")
            return []
    
    async def _enhance_with_ml(self, recommendations: List[Dict], request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Enhance recommendations using ML service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ml_service_url}/enhance-recommendations",
                    json={
                        "recommendations": recommendations,
                        "user_id": request.user_id,
                        "context": request.context
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    enhanced = response.json()
                    return enhanced.get("enhanced_recommendations", recommendations)
                else:
                    logger.warning("ML service unavailable, returning base recommendations")
                    return recommendations
                    
        except Exception as e:
            logger.warning(f"ML enhancement failed: {e}")
            return recommendations
    
    async def _find_similar_users(self, user_id: int) -> List[int]:
        """Find users with similar reading preferences"""
        # Implementation for finding similar users
        return []
    
    async def _get_user_preferred_books(self, user_id: int) -> List[Dict[str, Any]]:
        """Get books preferred by a user"""
        # Implementation for getting user's preferred books
        return []
    
    async def _find_similar_books(self, book_id: int) -> List[Dict[str, Any]]:
        """Find books similar to the given book"""
        # Implementation for finding similar books
        return []
    
    async def _get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get user's reading preferences"""
        # Implementation for getting user preferences
        return {}
    
    async def _find_books_by_preferences(self, preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find books matching user preferences"""
        # Implementation for finding books by preferences
        return []
    
    def _deduplicate_and_rank(self, recommendations: List[Dict], limit: int) -> List[Dict[str, Any]]:
        """Remove duplicates and rank recommendations"""
        seen = set()
        unique_recommendations = []
        
        for rec in recommendations:
            book_id = rec.get("id")
            if book_id and book_id not in seen:
                seen.add(book_id)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:limit]
    
    def _book_to_dict(self, book) -> Dict[str, Any]:
        """Convert book model to dictionary"""
        return {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
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

# FastAPI app for recommendation engine
app = FastAPI(
    title="Recommendation Engine",
    description="Industrial-grade recommendation system",
    version="1.0.0"
)

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get recommendations using the recommendation engine"""
    engine = RecommendationEngine(db)
    return await engine.get_recommendations(request)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "recommendation-engine"} 