#!/usr/bin/env python3
"""
MCP Server for Bkmrk'd AI Recommendation Engine
Provides agentic AI capabilities for book recommendations
"""

import asyncio
import json
import logging
import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai
import weaviate
from weaviate import Client
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini with proper configuration
# genai.configure(api_key=os.getenv("GEMINI_API_KEY")) # This line is no longer needed

# Configure the model with proper parameters
# model = genai.GenerativeModel( # This line is no longer needed
#     'gemini-pro',
#     generation_config=genai.types.GenerationConfig(
#         temperature=0.7,
#         top_p=0.9,
#         top_k=40,
#         max_output_tokens=2048,
#         candidate_count=1
#     )
# )

# System prompts for different tasks
SYSTEM_PROMPTS = {
    "recommendation": """
    You are an expert book recommendation AI. Your task is to provide personalized book recommendations based on user preferences and queries.
    
    Guidelines:
    1. Consider user preferences, reading history, and current interests
    2. Provide diverse recommendations across different genres
    3. Include reasoning for each recommendation
    4. Consider book ratings, popularity, and relevance
    5. Suggest both similar books and complementary reads
    6. Provide confidence scores for recommendations
    """,
    
    "search": """
    You are a book search assistant. Your task is to help users find books by analyzing their queries and providing relevant search results.
    
    Guidelines:
    1. Understand the user's search intent
    2. Identify key search terms and concepts
    3. Consider genre, author, title, and thematic elements
    4. Provide both exact matches and related suggestions
    5. Include book details like rating, price, and availability
    """,
    
    "enhancement": """
    You are a book information enhancement AI. Your task is to add additional context and information to book recommendations.
    
    Guidelines:
    1. Add book availability and pricing information
    2. Include series information and reading order
    3. Add reader reviews and ratings
    4. Provide purchase recommendations
    5. Suggest similar authors and books
    6. Include publication dates and editions
    """
}

# Initialize Weaviate
weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="MCP Server - AI Recommendation Engine")

class BookRecommendationRequest(BaseModel):
    user_id: Optional[int] = None
    book_id: Optional[int] = None
    user_preferences: Optional[List[str]] = None
    limit: int = 10

class BookRecommendationResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    reasoning: str
    confidence: float

class BookEmbeddingRequest(BaseModel):
    book_id: int
    title: str
    author: str
    description: str
    genre: str

class BookEmbeddingResponse(BaseModel):
    success: bool
    message: str

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server"""
    try:
        # Initialize Weaviate schema
        await initialize_weaviate_schema()
        logger.info("✅ MCP Server started successfully")
    except Exception as e:
        logger.error(f"❌ MCP Server startup failed: {e}")
        raise

async def initialize_weaviate_schema():
    """Initialize Weaviate schema for book embeddings"""
    try:
        # Check if Book class exists
        schema = client.schema.get()
        book_class_exists = any(
            class_obj["class"] == "Book" 
            for class_obj in schema.get("classes", [])
        )
        
        if not book_class_exists:
            # Create Book class schema
            class_obj = {
                "class": "Book",
                "vectorizer": "text2vec-transformers",
                "properties": [
                    {
                        "name": "book_id",
                        "dataType": ["int"],
                        "description": "Unique book identifier"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Book title"
                    },
                    {
                        "name": "author",
                        "dataType": ["text"],
                        "description": "Book author"
                    },
                    {
                        "name": "description",
                        "dataType": ["text"],
                        "description": "Book description"
                    },
                    {
                        "name": "genre",
                        "dataType": ["text"],
                        "description": "Book genre"
                    },
                    {
                        "name": "rating",
                        "dataType": ["number"],
                        "description": "Book rating"
                    },
                    {
                        "name": "price",
                        "dataType": ["number"],
                        "description": "Book price"
                    }
                ]
            }
            
            client.schema.create_class(class_obj)
            logger.info("✅ Weaviate Book schema created")
        else:
            logger.info("✅ Weaviate Book schema already exists")
            
    except Exception as e:
        logger.error(f"❌ Error initializing Weaviate schema: {e}")
        raise

@app.post("/embed-book", response_model=BookEmbeddingResponse)
async def embed_book(request: BookEmbeddingRequest):
    """Embed a book into the vector database"""
    try:
        # Create book text for embedding
        book_text = f"Title: {request.title}\nAuthor: {request.author}\nGenre: {request.genre}\nDescription: {request.description}"
        
        # Add book to Weaviate
        client.data_object.create(
            class_name="Book",
            data_object={
                "book_id": request.book_id,
                "title": request.title,
                "author": request.author,
                "description": request.description,
                "genre": request.genre,
                "rating": 0.0,
                "price": 0.0
            }
        )
        
        logger.info(f"✅ Book {request.book_id} embedded successfully")
        return BookEmbeddingResponse(success=True, message="Book embedded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error embedding book: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommendations", response_model=BookRecommendationResponse)
async def get_recommendations(request: BookRecommendationRequest):
    """Get AI-powered book recommendations"""
    try:
        # Build dynamic context
        context = await build_recommendation_context(request)
        
        # Generate AI recommendations
        prompt = f"""
        {SYSTEM_PROMPTS['recommendation']}
        
        Context: {context}
        
        User Request: {request.user_preferences or 'General recommendations'}
        Limit: {request.limit}
        
        Please provide {request.limit} book recommendations in JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Book Title",
                    "author": "Author Name",
                    "genre": "Genre",
                    "reasoning": "Why this book is recommended",
                    "confidence": 0.95
                }}
            ],
            "reasoning": "Overall reasoning for recommendations",
            "confidence": 0.9
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPTS["recommendation"]},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2048
        )
        recommendations_data = parse_recommendations(response.choices[0].message.content)
        
        # Enhance with vector search
        enhanced_recommendations = await enhance_with_vector_search(
            recommendations_data.get("recommendations", []), 
            request
        )
        
        return BookRecommendationResponse(
            recommendations=enhanced_recommendations,
            reasoning=recommendations_data.get("reasoning", ""),
            confidence=recommendations_data.get("confidence", 0.8)
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def build_recommendation_context(request: BookRecommendationRequest) -> str:
    """Build dynamic context for recommendations"""
    context_parts = []
    
    if request.user_id:
        # Get user reading history
        user_history = get_user_reading_history(request.user_id)
        if user_history:
            context_parts.append(f"User Reading History: {', '.join(user_history)}")
    
    if request.book_id:
        # Get book details
        book_details = get_book_details_from_db(request.book_id)
        if book_details:
            context_parts.append(f"Reference Book: {book_details['title']} by {book_details['author']} ({book_details['genre']})")
    
    # Get trending books
    trending_books = get_trending_books()
    if trending_books:
        context_parts.append(f"Trending Books: {', '.join(trending_books)}")
    
    # Get popular genres
    popular_genres = get_popular_genres()
    if popular_genres:
        context_parts.append(f"Popular Genres: {', '.join(popular_genres)}")
    
    # Get market context
    market_context = get_market_context()
    if market_context:
        context_parts.append(f"Market Context: {market_context}")
    
    return "\n".join(context_parts) if context_parts else "General book recommendations"

async def enhance_with_vector_search(
    ai_recommendations: List[Dict], 
    request: BookRecommendationRequest
) -> List[Dict]:
    """Enhance AI recommendations with vector search results"""
    try:
        vector_results = []
        
        if request.book_id:
            # Search for similar books by book ID
            vector_results = await search_similar_books_by_id(request.book_id, request.limit)
        elif request.user_preferences:
            # Search by user preferences
            search_text = " ".join(request.user_preferences)
            vector_results = await search_books_by_text(search_text, request.limit)
        else:
            # Get popular books from vector DB
            vector_results = await get_popular_books_from_vector_db(request.limit)
        
        # Combine and rank results
        combined_results = ai_recommendations + vector_results
        
        # Remove duplicates and rank
        final_results = remove_duplicates_and_rank(combined_results, request.limit)
        
        return final_results
        
    except Exception as e:
        logger.error(f"Error enhancing with vector search: {e}")
        return ai_recommendations

async def search_similar_books_by_id(book_id: int, limit: int) -> List[Dict[str, Any]]:
    """Search for similar books using vector database"""
    try:
        # Get book details from vector DB
        book_details = await get_book_details_from_vector_db(book_id)
        if not book_details:
            return []
        
        # Search for similar books
        result = client.query.get("Book", [
            "book_id", "title", "author", "genre", "rating", "price"
        ]).with_near_vector({
            "vector": book_details.get("vector", [])
        }).with_limit(limit).do()
        
        books = result.get("data", {}).get("Get", {}).get("Book", [])
        return [
            {
                "id": book["book_id"],
                "title": book["title"],
                "author": book["author"],
                "genre": book["genre"],
                "rating": book.get("rating", 0.0),
                "price": book.get("price", 0.0),
                "source": "vector_search",
                "confidence": calculate_similarity_confidence(book.get("_additional", {}).get("distance", 0.0))
            }
            for book in books
        ]
        
    except Exception as e:
        logger.error(f"Error searching similar books: {e}")
        return []

async def search_books_by_text(text: str, limit: int) -> List[Dict[str, Any]]:
    """Search books by text using vector database"""
    try:
        result = client.query.get("Book", [
            "book_id", "title", "author", "genre", "rating", "price"
        ]).with_near_text({
            "concepts": [text]
        }).with_limit(limit).do()
        
        books = result.get("data", {}).get("Get", {}).get("Book", [])
        return [
            {
                "id": book["book_id"],
                "title": book["title"],
                "author": book["author"],
                "genre": book["genre"],
                "rating": book.get("rating", 0.0),
                "price": book.get("price", 0.0),
                "source": "text_search",
                "confidence": 0.8
            }
            for book in books
        ]
        
    except Exception as e:
        logger.error(f"Error searching books by text: {e}")
        return []

async def get_popular_books_from_vector_db(limit: int) -> List[Dict[str, Any]]:
    """Get popular books from vector database"""
    try:
        result = client.query.get("Book", [
            "book_id", "title", "author", "genre", "rating", "price"
        ]).with_sort([
            {
                "path": ["rating"],
                "order": "desc"
            }
        ]).with_limit(limit).do()
        
        books = result.get("data", {}).get("Get", {}).get("Book", [])
        return [
            {
                "id": book["book_id"],
                "title": book["title"],
                "author": book["author"],
                "genre": book["genre"],
                "rating": book.get("rating", 0.0),
                "price": book.get("price", 0.0),
                "source": "popular_books",
                "confidence": 0.7
            }
            for book in books
        ]
        
    except Exception as e:
        logger.error(f"Error getting popular books: {e}")
        return []

async def get_book_details_from_vector_db(book_id: int) -> Dict[str, Any]:
    """Get book details from vector database"""
    try:
        result = client.query.get("Book", [
            "book_id", "title", "author", "genre", "rating", "price", "_additional {vector}"
        ]).with_where({
            "path": ["book_id"],
            "operator": "Equal",
            "valueInt": book_id
        }).do()
        
        books = result.get("data", {}).get("Get", {}).get("Book", [])
        if books:
            return books[0]
        return {}
        
    except Exception as e:
        logger.error(f"Error getting book details from vector DB: {e}")
        return {}

def calculate_similarity_confidence(similarity_score: float) -> float:
    """Calculate confidence based on similarity score"""
    # Convert distance to confidence (lower distance = higher confidence)
    return max(0.1, 1.0 - similarity_score)

def remove_duplicates_and_rank(recommendations: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Remove duplicates and rank recommendations"""
    seen_titles = set()
    unique_recommendations = []
    
    for rec in recommendations:
        title_key = f"{rec.get('title', '')}-{rec.get('author', '')}"
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_recommendations.append(rec)
    
    # Sort by confidence and return top results
    unique_recommendations.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
    return unique_recommendations[:limit]

# Mock functions for database operations
def get_user_reading_history(user_id: int) -> List[str]:
    """Get user's reading history (mock implementation)"""
    return ["The Great Gatsby", "1984", "To Kill a Mockingbird"]

def get_book_details_from_db(book_id: int) -> Dict[str, Any]:
    """Get book details from database (mock implementation)"""
    return {
        "title": "Sample Book",
        "author": "Sample Author",
        "genre": "Fiction"
    }

def get_trending_books() -> List[str]:
    """Get trending books (mock implementation)"""
    return ["The Midnight Library", "Klara and the Sun", "Project Hail Mary"]

def get_popular_genres() -> List[str]:
    """Get popular genres (mock implementation)"""
    return ["Fiction", "Mystery", "Science Fiction", "Romance"]

def get_market_context() -> str:
    """Get market context (mock implementation)"""
    return "Current market trends favor dystopian fiction and self-help books"

def parse_recommendations(content: str) -> Dict[str, Any]:
    """Parse recommendations from AI response"""
    try:
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        # Fallback: parse structured text
        recommendations = []
        lines = content.split('\n')
        current_rec = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('"title"') or line.startswith('title'):
                current_rec['title'] = line.split(':')[1].strip().strip('"')
            elif line.startswith('"author"') or line.startswith('author'):
                current_rec['author'] = line.split(':')[1].strip().strip('"')
            elif line.startswith('"genre"') or line.startswith('genre'):
                current_rec['genre'] = line.split(':')[1].strip().strip('"')
            elif line.startswith('"confidence"') or line.startswith('confidence'):
                current_rec['confidence'] = float(line.split(':')[1].strip())
                if current_rec:
                    recommendations.append(current_rec)
                    current_rec = {}
        
        return {
            "recommendations": recommendations,
            "reasoning": "AI-generated recommendations",
            "confidence": 0.8
        }
        
    except Exception as e:
        logger.error(f"Error parsing recommendations: {e}")
        return {
            "recommendations": [],
            "reasoning": "Failed to parse recommendations",
            "confidence": 0.5
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Weaviate connection
        client.schema.get()
        return {"status": "healthy", "weaviate": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 