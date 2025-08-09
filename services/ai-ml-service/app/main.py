#!/usr/bin/env python3
"""
Consolidated AI/ML Service for Bkmrk'd Bookstore
Combines recommendation engine, analytics, and vector search capabilities
"""

import os
import logging
import json
import time
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import google.generativeai as genai
import weaviate
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import pandas as pd
import numpy as np

# RAGAS imports
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_relevancy
from datasets import Dataset
from sentence_transformers import SentenceTransformer

# Web Search and Agentic Tools
import requests
import aiohttp
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import wikipedia
from newsapi import NewsApiClient

# LangChain for Agentic Tools
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_service.log')
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

# Global variables
gemini_model = None
weaviate_client = None
redis_client = None
db_engine = None
SessionLocal = None
embedding_model = None

# Pydantic models
class RecommendationRequest(BaseModel):
    user_id: Optional[int] = Field(None, description="User ID for personalized recommendations")
    book_id: Optional[int] = Field(None, description="Reference book ID for similar recommendations")
    user_preferences: Optional[List[str]] = Field(None, description="User genre preferences")
    limit: int = Field(10, ge=1, le=50, description="Number of recommendations to return")
    strategy: str = Field("ai_powered", description="Recommendation strategy: ai_powered, collaborative, content_based")

class RecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    reasoning: str
    confidence: float
    metadata: Dict[str, Any]
    processing_time: float

class AnalyticsRequest(BaseModel):
    recommendations_data: List[Dict[str, Any]]
    evaluation_type: str = Field("ragas", description="Type of evaluation: ragas, quality, both")

class AnalyticsResponse(BaseModel):
    evaluation_results: Dict[str, float]
    quality_analysis: Dict[str, Any]
    processing_time: float

class VectorSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Number of results")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold")

class VectorSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query_embedding: List[float]
    processing_time: float

class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of results")
    search_type: str = Field("web", description="Search type: web, news, wikipedia")

class WebSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    query: str
    search_type: str
    processing_time: float

class AgenticRequest(BaseModel):
    task: str = Field(..., description="Task to perform")
    context: Optional[str] = Field(None, description="Additional context")
    tools: List[str] = Field(["web_search", "wikipedia", "news"], description="Tools to use")

class AgenticResponse(BaseModel):
    result: str
    reasoning: str
    tools_used: List[str]
    processing_time: float

class BookAnalysisRequest(BaseModel):
    book_title: str = Field(..., description="Book title to analyze")
    analysis_type: str = Field("comprehensive", description="Analysis type: comprehensive, market, reviews")

class BookAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    sources: List[str]
    processing_time: float

# Initialize Gemini model
def get_gemini_model():
    """Initialize Gemini model for AI tasks"""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(
        'gemini-pro',
        generation_config=genai.types.GenerationConfig(
            temperature=0.3,
            top_p=0.9,
            max_output_tokens=2048,
            candidate_count=1
        )
    )

# Initialize OpenAI LLM for agentic tools
def get_gemini_llm():
    """Initialize Gemini LLM for agentic tools"""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        logger.warning("GEMINI_API_KEY not set - agentic tools will be limited")
        return None
    
    return ChatGoogleGenerativeAI(
        model="gemini-pro",
        google_api_key=gemini_api_key,
        temperature=0.3,
        max_tokens=1000
    )

def get_openai_llm():
    """Initialize OpenAI LLM for agentic tools (fallback)"""
    if not OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set - agentic tools will be limited")
        return None
    
    return OpenAI(
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3,
        max_tokens=1000
    )

class BookService:
    """Production book data service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_books_data(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get books data from database with proper error handling"""
        try:
            query = text("""
                SELECT id, title, author, description, genre, rating, price, 
                       publication_date, isbn, language, pages, publisher,
                       created_at, updated_at
                FROM books 
                WHERE active = true
                ORDER BY rating DESC, created_at DESC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {"limit": limit})
            books = []
            
            for row in result:
                books.append({
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "description": row.description,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0,
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "isbn": row.isbn,
                    "language": row.language,
                    "pages": row.pages,
                    "publisher": row.publisher,
                    "created_at": str(row.created_at) if row.created_at else None,
                    "updated_at": str(row.updated_at) if row.updated_at else None
                })
            
            logger.info(f"Retrieved {len(books)} books from database")
            return books
            
        except Exception as e:
            logger.error(f"Database error fetching books: {e}")
            raise HTTPException(status_code=500, detail="Database connection failed")
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        """Get specific book by ID with validation"""
        try:
            query = text("""
                SELECT id, title, author, description, genre, rating, price, 
                       publication_date, isbn, language, pages, publisher
                FROM books 
                WHERE id = :book_id AND active = true
            """)
            
            result = self.db.execute(query, {"book_id": book_id})
            row = result.fetchone()
            
            if row:
                return {
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "description": row.description,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0,
                    "publication_date": str(row.publication_date) if row.publication_date else None,
                    "isbn": row.isbn,
                    "language": row.language,
                    "pages": row.pages,
                    "publisher": row.publisher
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Database error fetching book {book_id}: {e}")
            return None
    
    def get_user_preferences(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user reading preferences and history"""
        try:
            query = text("""
                SELECT b.genre, COUNT(*) as read_count, AVG(r.rating) as avg_rating
                FROM user_books ub
                JOIN books b ON ub.book_id = b.id
                LEFT JOIN ratings r ON ub.book_id = r.book_id AND ub.user_id = r.user_id
                WHERE ub.user_id = :user_id
                GROUP BY b.genre
                ORDER BY read_count DESC, avg_rating DESC
                LIMIT 10
            """)
            
            result = self.db.execute(query, {"user_id": user_id})
            preferences = []
            
            for row in result:
                preferences.append({
                    "genre": row.genre,
                    "read_count": row.read_count,
                    "avg_rating": float(row.avg_rating) if row.avg_rating else 0.0
                })
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return []

class RecommendationEngine:
    """Production recommendation engine with multiple strategies"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.book_service = BookService(db_session)
        self.cache_client = redis_client
        self.embedding_model = embedding_model
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get recommendations using specified strategy"""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"recommendations:{request.strategy}:{request.user_id}:{request.book_id}:{request.limit}"
            
            if self.cache_client:
                cached = self.cache_client.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for recommendations: {cache_key}")
                    return RecommendationResponse(**json.loads(cached))
            
            # Get recommendations based on strategy
            if request.strategy == "ai_powered":
                recommendations = await self._get_ai_recommendations(request)
            elif request.strategy == "collaborative":
                recommendations = await self._get_collaborative_recommendations(request)
            elif request.strategy == "content_based":
                recommendations = await self._get_content_based_recommendations(request)
            else:
                raise HTTPException(status_code=400, detail="Invalid strategy")
            
            processing_time = time.time() - start_time
            
            response = RecommendationResponse(
                recommendations=recommendations,
                reasoning=f"Generated using {request.strategy} strategy",
                confidence=self._calculate_confidence(recommendations),
                metadata={
                    "strategy": request.strategy,
                    "user_id": request.user_id,
                    "book_id": request.book_id,
                    "processing_time": processing_time,
                    "recommendations_count": len(recommendations)
                },
                processing_time=processing_time
            )
            
            # Cache response for 15 minutes
            if self.cache_client:
                self.cache_client.setex(cache_key, 900, json.dumps(response.dict()))
            
            logger.info(f"Generated {len(recommendations)} recommendations in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise HTTPException(status_code=500, detail="Recommendation generation failed")
    
    async def _get_ai_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Generate AI-powered recommendations using Gemini"""
        try:
            books_data = self.book_service.get_books_data(limit=500)
            
            if not books_data:
                raise HTTPException(status_code=500, detail="No books data available")
            
            # Build context
            context = self._build_ai_context(request, books_data)
            
            # Generate AI recommendations
            prompt = self._create_ai_prompt(request, books_data, context)
            
            response = gemini_model.generate_content(prompt)
            result = json.loads(response.text)
            
            # Map to real book data
            recommendations = self._map_ai_recommendations(result.get("recommendations", []), books_data)
            
            return recommendations[:request.limit]
            
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return []
    
    async def _get_collaborative_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Generate collaborative filtering recommendations"""
        try:
            if not request.user_id:
                raise HTTPException(status_code=400, detail="User ID required for collaborative filtering")
            
            # Get similar users
            similar_users = self._find_similar_users(request.user_id)
            
            # Get books liked by similar users
            recommendations = self._get_books_from_similar_users(similar_users, request.user_id)
            
            return recommendations[:request.limit]
            
        except Exception as e:
            logger.error(f"Collaborative recommendation error: {e}")
            return []
    
    async def _get_content_based_recommendations(self, request: RecommendationRequest) -> List[Dict[str, Any]]:
        """Generate content-based recommendations"""
        try:
            books_data = self.book_service.get_books_data(limit=1000)
            
            if request.book_id:
                # Similar books based on reference book
                reference_book = self.book_service.get_book_by_id(request.book_id)
                if reference_book:
                    recommendations = self._find_similar_books(reference_book, books_data)
                else:
                    recommendations = []
            else:
                # Based on user preferences
                user_prefs = self.book_service.get_user_preferences(request.user_id) if request.user_id else []
                recommendations = self._recommend_by_preferences(user_prefs, books_data)
            
            return recommendations[:request.limit]
            
        except Exception as e:
            logger.error(f"Content-based recommendation error: {e}")
            return []
    
    def _build_ai_context(self, request: RecommendationRequest, books_data: List[Dict]) -> str:
        """Build comprehensive context for AI recommendations"""
        context_parts = []
        
        if request.user_id:
            user_prefs = self.book_service.get_user_preferences(request.user_id)
            if user_prefs:
                context_parts.append(f"User reading history: {', '.join([p['genre'] for p in user_prefs[:5]])}")
        
        if request.user_preferences:
            context_parts.append(f"User preferences: {', '.join(request.user_preferences)}")
        
        if request.book_id:
            book = self.book_service.get_book_by_id(request.book_id)
            if book:
                context_parts.append(f"Reference book: {book['title']} by {book['author']} (Genre: {book['genre']})")
        
        # Dataset statistics
        genres = [book['genre'] for book in books_data if book['genre']]
        avg_rating = sum(book['rating'] for book in books_data) / len(books_data) if books_data else 0
        
        context_parts.append(f"Available: {len(books_data)} books, {len(set(genres))} genres, avg rating: {avg_rating:.2f}")
        
        return "; ".join(context_parts) if context_parts else "General recommendations"
    
    def _create_ai_prompt(self, request: RecommendationRequest, books_data: List[Dict], context: str) -> str:
        """Create detailed AI prompt for recommendations"""
        sample_books = books_data[:30]
        books_context = "\n".join([
            f"- {book['title']} by {book['author']} (Genre: {book['genre']}, Rating: {book['rating']:.1f}, Price: ${book['price']:.2f})"
            for book in sample_books
        ])
        
        return f"""
        You are an expert book recommendation AI for Bkmrk'd Bookstore. Generate {request.limit} personalized book recommendations.
        
        Context: {context}
        
        Available Books Sample:
        {books_context}
        
        Consider:
        - User preferences and reading history
        - Book ratings and popularity
        - Genre diversity
        - Price range
        - Publication recency
        
        Return recommendations in this exact JSON format:
        {{
            "recommendations": [
                {{
                    "book_id": 123,
                    "title": "Book Title",
                    "author": "Author Name",
                    "genre": "Genre",
                    "rating": 4.5,
                    "price": 19.99,
                    "reasoning": "Detailed explanation of why this book is recommended",
                    "confidence": 0.85
                }}
            ]
        }}
        
        Ensure all book titles and authors match exactly with the available books list.
        """
    
    def _map_ai_recommendations(self, ai_recommendations: List[Dict], books_data: List[Dict]) -> List[Dict[str, Any]]:
        """Map AI recommendations to real book data"""
        mapped_recommendations = []
        
        for ai_rec in ai_recommendations:
            # Find matching book by title and author
            matching_book = next(
                (book for book in books_data 
                 if book['title'].lower() == ai_rec['title'].lower() 
                 and book['author'].lower() == ai_rec['author'].lower()),
                None
            )
            
            if matching_book:
                mapped_recommendations.append({
                    "book_id": matching_book['id'],
                    "title": matching_book['title'],
                    "author": matching_book['author'],
                    "genre": matching_book['genre'],
                    "rating": matching_book['rating'],
                    "price": matching_book['price'],
                    "description": matching_book['description'],
                    "reasoning": ai_rec.get('reasoning', 'AI recommended'),
                    "confidence": ai_rec.get('confidence', 0.8)
                })
        
        return mapped_recommendations
    
    def _find_similar_users(self, user_id: int) -> List[int]:
        """Find users with similar reading preferences"""
        try:
            query = text("""
                SELECT DISTINCT ub2.user_id, COUNT(*) as common_books
                FROM user_books ub1
                JOIN user_books ub2 ON ub1.book_id = ub2.book_id
                WHERE ub1.user_id = :user_id AND ub2.user_id != :user_id
                GROUP BY ub2.user_id
                ORDER BY common_books DESC
                LIMIT 10
            """)
            
            result = self.db.execute(query, {"user_id": user_id})
            return [row.user_id for row in result]
            
        except Exception as e:
            logger.error(f"Error finding similar users: {e}")
            return []
    
    def _get_books_from_similar_users(self, similar_users: List[int], exclude_user_id: int) -> List[Dict[str, Any]]:
        """Get books liked by similar users"""
        try:
            if not similar_users:
                return []
            
            query = text("""
                SELECT b.id, b.title, b.author, b.genre, b.rating, b.price, b.description,
                       COUNT(*) as user_count, AVG(r.rating) as avg_rating
                FROM user_books ub
                JOIN books b ON ub.book_id = b.id
                LEFT JOIN ratings r ON ub.book_id = r.book_id
                WHERE ub.user_id = ANY(:user_ids) 
                  AND ub.book_id NOT IN (
                      SELECT book_id FROM user_books WHERE user_id = :exclude_user_id
                  )
                GROUP BY b.id, b.title, b.author, b.genre, b.rating, b.price, b.description
                ORDER BY user_count DESC, avg_rating DESC
                LIMIT 20
            """)
            
            result = self.db.execute(query, {"user_ids": similar_users, "exclude_user_id": exclude_user_id})
            recommendations = []
            
            for row in result:
                recommendations.append({
                    "book_id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "genre": row.genre,
                    "rating": float(row.rating) if row.rating else 0.0,
                    "price": float(row.price) if row.price else 0.0,
                    "description": row.description,
                    "reasoning": f"Liked by {row.user_count} similar users",
                    "confidence": min(0.9, row.user_count / 10.0)
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting books from similar users: {e}")
            return []
    
    def _find_similar_books(self, reference_book: Dict[str, Any], books_data: List[Dict]) -> List[Dict[str, Any]]:
        """Find books similar to reference book"""
        similar_books = []
        
        for book in books_data:
            if book['id'] == reference_book['id']:
                continue
            
            similarity_score = 0
            
            # Genre similarity
            if book['genre'] == reference_book['genre']:
                similarity_score += 0.4
            
            # Rating similarity
            rating_diff = abs(book['rating'] - reference_book['rating'])
            if rating_diff <= 1.0:
                similarity_score += 0.3
            
            # Price similarity
            price_diff = abs(book['price'] - reference_book['price'])
            if price_diff <= 5.0:
                similarity_score += 0.2
            
            # Author similarity
            if book['author'] == reference_book['author']:
                similarity_score += 0.1
            
            if similarity_score > 0.3:
                similar_books.append({
                    **book,
                    "reasoning": f"Similar to {reference_book['title']}",
                    "confidence": similarity_score
                })
        
        return sorted(similar_books, key=lambda x: x['confidence'], reverse=True)
    
    def _recommend_by_preferences(self, user_prefs: List[Dict], books_data: List[Dict]) -> List[Dict[str, Any]]:
        """Recommend books based on user preferences"""
        if not user_prefs:
            return []
        
        # Get top genres
        top_genres = [pref['genre'] for pref in user_prefs[:3]]
        
        recommendations = []
        for book in books_data:
            if book['genre'] in top_genres and book['rating'] >= 4.0:
                recommendations.append({
                    **book,
                    "reasoning": f"Matches your preference for {book['genre']}",
                    "confidence": 0.8
                })
        
        return sorted(recommendations, key=lambda x: x['rating'], reverse=True)
    
    def _calculate_confidence(self, recommendations: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence score"""
        if not recommendations:
            return 0.0
        
        confidences = [rec.get('confidence', 0.5) for rec in recommendations]
        return sum(confidences) / len(confidences)

class RAGASAnalytics:
    """Production RAGAS analytics for LLM evaluation"""
    
    def __init__(self):
        self.embedding_model_name = EMBEDDING_MODEL
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.metrics = [faithfulness, answer_relevancy, context_relevancy]
        
        logger.info(f"RAGAS Analytics initialized with model: {self.embedding_model_name}")
    
    def create_evaluation_dataset(self, recommendations_data: List[Dict]) -> Dataset:
        """Create evaluation dataset from recommendation data"""
        try:
            eval_data = []
            
            for rec_data in recommendations_data:
                question = rec_data.get("user_query", "Book recommendation request")
                context = rec_data.get("context", [])
                answer = rec_data.get("recommendation_explanation", "")
                ground_truth = rec_data.get("ground_truth", "")
                
                eval_data.append({
                    "question": question,
                    "contexts": context,
                    "answer": answer,
                    "ground_truth": ground_truth
                })
            
            dataset = Dataset.from_list(eval_data)
            logger.info(f"Created evaluation dataset with {len(eval_data)} samples")
            return dataset
            
        except Exception as e:
            logger.error(f"Error creating evaluation dataset: {e}")
            return None
    
    def evaluate_recommendations(self, dataset: Dataset) -> Dict[str, float]:
        """Evaluate recommendations using RAGAS metrics"""
        try:
            logger.info("Starting RAGAS evaluation...")
            
            results = evaluate(dataset, self.metrics)
            
            evaluation_results = {}
            for metric_name, metric_value in results.items():
                evaluation_results[metric_name] = float(metric_value)
            
            logger.info(f"RAGAS evaluation completed: {evaluation_results}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error in RAGAS evaluation: {e}")
            return {}
    
    def analyze_recommendation_quality(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Analyze recommendation quality using real data"""
        try:
            if not recommendations:
                return {"error": "No recommendations to analyze"}
            
            # Calculate diversity
            genres = [rec.get("genre", "unknown") for rec in recommendations]
            unique_genres = len(set(genres))
            diversity_score = unique_genres / len(recommendations) if recommendations else 0
            
            # Calculate average confidence and rating
            confidences = [rec.get("confidence", 0) for rec in recommendations]
            ratings = [rec.get("rating", 0) for rec in recommendations]
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
            
            # Price analysis
            prices = [rec.get("price", 0) for rec in recommendations if rec.get("price")]
            price_range = max(prices) - min(prices) if prices else 0
            avg_price = sum(prices) / len(prices) if prices else 0
            
            # Author diversity
            authors = [rec.get("author", "unknown") for rec in recommendations]
            unique_authors = len(set(authors))
            author_diversity = unique_authors / len(recommendations) if recommendations else 0
            
            return {
                "diversity_score": diversity_score,
                "author_diversity": author_diversity,
                "average_confidence": avg_confidence,
                "average_rating": avg_rating,
                "average_price": avg_price,
                "price_range": price_range,
                "total_recommendations": len(recommendations),
                "unique_genres": unique_genres,
                "unique_authors": unique_authors,
                "genre_distribution": {genre: genres.count(genre) for genre in set(genres)},
                "author_distribution": {author: authors.count(author) for author in set(authors)}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing recommendation quality: {e}")
            return {"error": str(e)}

class VectorSearchService:
    """Production vector search service"""
    
    def __init__(self):
        self.weaviate_client = weaviate_client
        self.embedding_model = embedding_model
    
    async def search_books(self, request: VectorSearchRequest) -> VectorSearchResponse:
        """Search books using vector similarity"""
        start_time = time.time()
        
        try:
            # Generate embedding for query
            query_embedding = self.embedding_model.encode([request.query])[0].tolist()
            
            # Search in Weaviate
            if self.weaviate_client:
                results = self.weaviate_client.query.get("Book", [
                    "id", "title", "author", "genre", "rating", "price", "description"
                ]).with_near_vector({
                    "vector": query_embedding
                }).with_additional(["distance"]).do()
                
                books = []
                for result in results["data"]["Get"]["Book"]:
                    distance = result["_additional"]["distance"]
                    if distance <= (1 - request.similarity_threshold):
                        books.append({
                            "id": result["id"],
                            "title": result["title"],
                            "author": result["author"],
                            "genre": result["genre"],
                            "rating": result["rating"],
                            "price": result["price"],
                            "description": result["description"],
                            "similarity_score": 1 - distance
                        })
                
                processing_time = time.time() - start_time
                
                return VectorSearchResponse(
                    results=books[:request.limit],
                    query_embedding=query_embedding,
                    processing_time=processing_time
                )
            else:
                # Fallback to database search
                return await self._fallback_search(request, start_time)
                
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return await self._fallback_search(request, start_time)
    
    async def _fallback_search(self, request: VectorSearchRequest, start_time: float) -> VectorSearchResponse:
        """Fallback to database search when vector search fails"""
        try:
            # Simple text search in database
            query = text("""
                SELECT id, title, author, genre, rating, price, description
                FROM books
                WHERE title ILIKE :search_term 
                   OR author ILIKE :search_term 
                   OR description ILIKE :search_term
                ORDER BY rating DESC
                LIMIT :limit
            """)
            
            search_term = f"%{request.query}%"
            
            # This would need a database session, simplified for now
            results = []
            
            processing_time = time.time() - start_time
            
            return VectorSearchResponse(
                results=results,
                query_embedding=[],
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            return VectorSearchResponse(
                results=[],
                query_embedding=[],
                processing_time=time.time() - start_time
            )

class WebSearchService:
    """Web search service with multiple search engines"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.news_api = NewsApiClient(api_key=NEWS_API_KEY) if NEWS_API_KEY else None
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web using DuckDuckGo"""
        try:
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("body", ""),
                    "source": "DuckDuckGo"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    async def search_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search news using NewsAPI"""
        try:
            if not self.news_api:
                return []
            
            news_results = self.news_api.get_everything(
                q=query,
                language='en',
                sort_by='relevancy',
                page_size=max_results
            )
            
            results = []
            for article in news_results.get("articles", []):
                results.append({
                    "title": article.get("title", ""),
                    "link": article.get("url", ""),
                    "snippet": article.get("description", ""),
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "published_at": article.get("publishedAt", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"News search error: {e}")
            return []
    
    async def search_wikipedia(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search Wikipedia"""
        try:
            # Search Wikipedia
            search_results = wikipedia.search(query, results=max_results)
            
            results = []
            for title in search_results:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    results.append({
                        "title": page.title,
                        "link": page.url,
                        "snippet": wikipedia.summary(title, sentences=3),
                        "source": "Wikipedia"
                    })
                except Exception as e:
                    logger.warning(f"Error fetching Wikipedia page {title}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []

class AgenticToolsService:
    """Agentic tools service using LangChain"""
    
    def __init__(self, web_search_service: WebSearchService):
        self.web_search = web_search_service
        self.llm = get_gemini_llm()
        self.agent = None
        
        if self.llm:
            self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize LangChain agent with tools"""
        try:
            # Define tools
            tools = [
                Tool(
                    name="web_search",
                    func=self._web_search_tool,
                    description="Search the web for current information"
                ),
                Tool(
                    name="wikipedia_search",
                    func=self._wikipedia_tool,
                    description="Search Wikipedia for detailed information"
                ),
                Tool(
                    name="news_search",
                    func=self._news_tool,
                    description="Search recent news articles"
                )
            ]
            
            # Initialize agent
            self.agent = initialize_agent(
                tools,
                self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True
            )
            
            logger.info("Agentic tools initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing agentic tools: {e}")
    
    def _web_search_tool(self, query: str) -> str:
        """Web search tool for agent"""
        try:
            results = asyncio.run(self.web_search.search_web(query, max_results=3))
            if results:
                return json.dumps(results, indent=2)
            return "No web search results found."
        except Exception as e:
            return f"Web search error: {e}"
    
    def _wikipedia_tool(self, query: str) -> str:
        """Wikipedia search tool for agent"""
        try:
            results = asyncio.run(self.web_search.search_wikipedia(query, max_results=2))
            if results:
                return json.dumps(results, indent=2)
            return "No Wikipedia results found."
        except Exception as e:
            return f"Wikipedia search error: {e}"
    
    def _news_tool(self, query: str) -> str:
        """News search tool for agent"""
        try:
            results = asyncio.run(self.web_search.search_news(query, max_results=3))
            if results:
                return json.dumps(results, indent=2)
            return "No news results found."
        except Exception as e:
            return f"News search error: {e}"
    
    async def execute_task(self, task: str, context: str = None, tools: List[str] = None) -> Dict[str, Any]:
        """Execute a task using agentic tools"""
        start_time = time.time()
        
        try:
            if not self.agent:
                # Fallback to direct search
                results = await self._fallback_search(task, tools or ["web_search"])
                return {
                    "result": json.dumps(results, indent=2),
                    "reasoning": "Used direct search as agentic tools unavailable",
                    "tools_used": tools or ["web_search"],
                    "processing_time": time.time() - start_time
                }
            
            # Use LangChain agent
            full_task = task
            if context:
                full_task = f"Context: {context}\nTask: {task}"
            
            result = self.agent.run(full_task)
            
            return {
                "result": result,
                "reasoning": "Executed using LangChain agentic tools",
                "tools_used": tools or ["web_search", "wikipedia", "news"],
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Agentic task execution error: {e}")
            return {
                "result": f"Error executing task: {e}",
                "reasoning": "Task execution failed",
                "tools_used": [],
                "processing_time": time.time() - start_time
            }
    
    async def _fallback_search(self, query: str, tools: List[str]) -> List[Dict[str, Any]]:
        """Fallback search when agentic tools are unavailable"""
        results = []
        
        for tool in tools:
            try:
                if tool == "web_search":
                    results.extend(await self.web_search.search_web(query, max_results=3))
                elif tool == "wikipedia":
                    results.extend(await self.web_search.search_wikipedia(query, max_results=2))
                elif tool == "news":
                    results.extend(await self.web_search.search_news(query, max_results=3))
            except Exception as e:
                logger.error(f"Fallback search error for {tool}: {e}")
        
        return results

class BookAnalysisService:
    """Book analysis service using web search and AI"""
    
    def __init__(self, web_search_service: WebSearchService, gemini_model):
        self.web_search = web_search_service
        self.gemini_model = gemini_model
    
    async def analyze_book(self, book_title: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze a book using web search and AI"""
        start_time = time.time()
        
        try:
            # Search for book information
            search_results = await self.web_search.search_web(f"{book_title} book review analysis", max_results=5)
            news_results = await self.web_search.search_news(f"{book_title} book", max_results=3)
            wiki_results = await self.web_search.search_wikipedia(book_title, max_results=2)
            
            # Combine all results
            all_results = search_results + news_results + wiki_results
            
            # Create context for AI analysis
            context = self._create_analysis_context(all_results, book_title, analysis_type)
            
            # Generate AI analysis
            prompt = self._create_analysis_prompt(book_title, analysis_type, context)
            
            if self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                analysis = json.loads(response.text)
            else:
                analysis = self._fallback_analysis(all_results, book_title, analysis_type)
            
            processing_time = time.time() - start_time
            
            return {
                "analysis": analysis,
                "sources": [result.get("source", "Unknown") for result in all_results],
                "processing_time": processing_time
            }
            
        except Exception as e:
            logger.error(f"Book analysis error: {e}")
            return {
                "analysis": {"error": str(e)},
                "sources": [],
                "processing_time": time.time() - start_time
            }
    
    def _create_analysis_context(self, results: List[Dict], book_title: str, analysis_type: str) -> str:
        """Create context from search results"""
        context_parts = [f"Book: {book_title}"]
        context_parts.append(f"Analysis Type: {analysis_type}")
        
        for i, result in enumerate(results[:10], 1):
            context_parts.append(f"Source {i} ({result.get('source', 'Unknown')}):")
            context_parts.append(f"Title: {result.get('title', 'N/A')}")
            context_parts.append(f"Content: {result.get('snippet', 'N/A')}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, book_title: str, analysis_type: str, context: str) -> str:
        """Create AI prompt for book analysis"""
        if analysis_type == "comprehensive":
            analysis_focus = "comprehensive analysis including market position, reviews, author background, and cultural impact"
        elif analysis_type == "market":
            analysis_focus = "market analysis including sales performance, target audience, and competitive positioning"
        elif analysis_type == "reviews":
            analysis_focus = "review analysis including critical reception, reader feedback, and overall sentiment"
        else:
            analysis_focus = "general analysis"
        
        return f"""
        Analyze the book "{book_title}" based on the following information.
        
        Context:
        {context}
        
        Please provide a {analysis_focus} in the following JSON format:
        {{
            "book_title": "{book_title}",
            "analysis_type": "{analysis_type}",
            "summary": "Brief summary of the book",
            "market_position": "Market analysis and positioning",
            "critical_reception": "Critical reviews and reception",
            "target_audience": "Target audience analysis",
            "cultural_impact": "Cultural significance and impact",
            "recommendations": "Recommendations for readers",
            "confidence_score": 0.85
        }}
        
        Base your analysis on the provided sources and be objective in your assessment.
        """
    
    def _fallback_analysis(self, results: List[Dict], book_title: str, analysis_type: str) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable"""
        return {
            "book_title": book_title,
            "analysis_type": analysis_type,
            "summary": f"Analysis based on {len(results)} sources",
            "market_position": "Market analysis not available",
            "critical_reception": "Review analysis not available",
            "target_audience": "Audience analysis not available",
            "cultural_impact": "Impact analysis not available",
            "recommendations": "Recommendations not available",
            "confidence_score": 0.5,
            "sources_count": len(results)
        }

# Database dependency
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize services
recommendation_engine = None
ragas_analytics = None
vector_search_service = None
web_search_service = None
agentic_tools_service = None
book_analysis_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global gemini_model, openai_llm, weaviate_client, redis_client, db_engine, SessionLocal
    global recommendation_engine, ragas_analytics, vector_search_service, embedding_model
    global web_search_service, agentic_tools_service, book_analysis_service
    
    # Startup
    logger.info("Starting Bkmrk'd AI/ML Service...")
    try:
        # Initialize Gemini
        if GEMINI_API_KEY:
            gemini_model = get_gemini_model()
            logger.info("Gemini initialized successfully")
        else:
            logger.warning("GEMINI_API_KEY not set - AI features will be limited")
        
        # Initialize Gemini LLM for agentic tools
        gemini_llm = get_gemini_llm()
        if gemini_llm:
            logger.info("Gemini LLM for agentic tools initialized successfully")
        else:
            logger.warning("Gemini LLM not available - agentic tools will be limited")
        
        # Initialize OpenAI LLM (fallback)
        openai_llm = get_openai_llm()
        if openai_llm:
            logger.info("OpenAI LLM (fallback) initialized successfully")
        else:
            logger.warning("OpenAI LLM not available - agentic tools will be limited")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Embedding model loaded: {EMBEDDING_MODEL}")
        
        # Initialize Weaviate
        try:
            weaviate_client = weaviate.Client(WEAVIATE_URL)
            weaviate_client.is_ready()
            logger.info("Weaviate connected successfully")
        except Exception as e:
            logger.warning(f"Weaviate connection failed: {e}")
        
        # Initialize Redis
        try:
            redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
        
        # Initialize Database
        try:
            db_engine = create_engine(DATABASE_URL)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
            logger.info("Database connected successfully")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}")
        
        # Initialize services
        if SessionLocal:
            db_session = SessionLocal()
            recommendation_engine = RecommendationEngine(db_session)
            ragas_analytics = RAGASAnalytics()
            vector_search_service = VectorSearchService()
            web_search_service = WebSearchService()
            agentic_tools_service = AgenticToolsService(web_search_service)
            book_analysis_service = BookAnalysisService(web_search_service, gemini_model)
            db_session.close()
        
        logger.info("AI/ML Service started successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI/ML Service...")
    try:
        if redis_client:
            redis_client.close()
        if db_engine:
            db_engine.dispose()
        logger.info("AI/ML Service shutdown complete")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

app = FastAPI(
    title="Bkmrk'd AI/ML Service",
    description="Consolidated AI/ML service for book recommendations, analytics, and vector search",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Bkmrk'd AI/ML Service",
        "version": "2.0.0",
        "timestamp": time.time(),
        "components": {
            "gemini": gemini_model is not None,
            "weaviate": weaviate_client is not None,
            "redis": redis_client is not None,
            "database": db_engine is not None,
            "embedding_model": embedding_model is not None
        }
    }

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest, db: Session = Depends(get_db)):
    """Get AI-powered recommendations using real data"""
    if not recommendation_engine:
        # Create new engine with current session
        recommendation_engine = RecommendationEngine(db)
    
    return await recommendation_engine.get_recommendations(request)

@app.post("/analytics", response_model=AnalyticsResponse)
async def analyze_recommendations(request: AnalyticsRequest):
    """Analyze recommendation performance using RAGAS"""
    start_time = time.time()
    
    if not ragas_analytics:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        evaluation_results = {}
        quality_analysis = {}
        
        if request.evaluation_type in ["ragas", "both"]:
            # Create evaluation dataset
            dataset = ragas_analytics.create_evaluation_dataset(request.recommendations_data)
            if dataset:
                evaluation_results = ragas_analytics.evaluate_recommendations(dataset)
        
        if request.evaluation_type in ["quality", "both"]:
            # Analyze quality
            quality_analysis = ragas_analytics.analyze_recommendation_quality(request.recommendations_data)
        
        processing_time = time.time() - start_time
        
        return AnalyticsResponse(
            evaluation_results=evaluation_results,
            quality_analysis=quality_analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error in analytics: {e}")
        raise HTTPException(status_code=500, detail="Analytics failed")

@app.post("/vector-search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest):
    """Search books using vector similarity"""
    if not vector_search_service:
        raise HTTPException(status_code=503, detail="Vector search service not available")
    
    return await vector_search_service.search_books(request)

@app.post("/web-search", response_model=WebSearchResponse)
async def search_web(request: WebSearchRequest):
    """Search the web using multiple engines"""
    start_time = time.time()
    
    if not web_search_service:
        raise HTTPException(status_code=503, detail="Web search service not available")
    
    try:
        if request.search_type == "web":
            results = await web_search_service.search_web(request.query, request.max_results)
        elif request.search_type == "news":
            results = await web_search_service.search_news(request.query, request.max_results)
        elif request.search_type == "wikipedia":
            results = await web_search_service.search_wikipedia(request.query, request.max_results)
        else:
            # Combined search
            web_results = await web_search_service.search_web(request.query, request.max_results // 2)
            news_results = await web_search_service.search_news(request.query, request.max_results // 2)
            results = web_results + news_results
        
        processing_time = time.time() - start_time
        
        return WebSearchResponse(
            results=results,
            query=request.query,
            search_type=request.search_type,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail="Web search failed")

@app.post("/agentic", response_model=AgenticResponse)
async def execute_agentic_task(request: AgenticRequest):
    """Execute a task using agentic tools"""
    if not agentic_tools_service:
        raise HTTPException(status_code=503, detail="Agentic tools service not available")
    
    try:
        result = await agentic_tools_service.execute_task(
            request.task,
            request.context,
            request.tools
        )
        
        return AgenticResponse(**result)
        
    except Exception as e:
        logger.error(f"Agentic task error: {e}")
        raise HTTPException(status_code=500, detail="Agentic task failed")

@app.post("/book-analysis", response_model=BookAnalysisResponse)
async def analyze_book(request: BookAnalysisRequest):
    """Analyze a book using web search and AI"""
    if not book_analysis_service:
        raise HTTPException(status_code=503, detail="Book analysis service not available")
    
    try:
        result = await book_analysis_service.analyze_book(
            request.book_title,
            request.analysis_type
        )
        
        return BookAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Book analysis error: {e}")
        raise HTTPException(status_code=500, detail="Book analysis failed")

@app.get("/mcp/health")
async def mcp_health_check():
    """MCP server health check"""
    return {
        "status": "healthy",
        "service": "Consolidated AI/ML Service",
        "capabilities": [
            "book_recommendations",
            "vector_search",
            "analytics",
            "embeddings",
            "web_search",
            "news_search",
            "wikipedia_search",
            "agentic_tools",
            "book_analysis",
            "langchain_integration",
            "collaborative_filtering",
            "content_based_filtering"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8003")),
        log_level="info"
    ) 