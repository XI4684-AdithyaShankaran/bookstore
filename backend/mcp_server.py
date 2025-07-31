#!/usr/bin/env python3
"""
MCP Server for Bkmrk'd AI Recommendation Engine
Provides agentic AI capabilities for book recommendations
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os

import google.generativeai as genai
from weaviate import Client, WeaviateClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from duckduckgo_search import DDGS
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Initialize Weaviate
weaviate_client = Client(
    url=WEAVIATE_URL,
    auth_client_secret=WEAVIATE_API_KEY,
    additional_headers={
        "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "")
    }
)

# Initialize Sentence Transformer for embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@dataclass
class BookState:
    """State for book recommendation pipeline"""
    user_id: Optional[int] = None
    user_preferences: Optional[Dict] = None
    current_books: Optional[List[Dict]] = None
    recommendations: Optional[List[Dict]] = None
    reasoning: Optional[str] = None
    context: Optional[Dict] = None

class BookRecommendationAgent:
    """Agentic AI for book recommendations"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.7,
            google_api_key=GEMINI_API_KEY
        )
        self.setup_weaviate_schema()
    
    def setup_weaviate_schema(self):
        """Setup Weaviate schema for books"""
        try:
            # Create book class schema
            book_class = {
                "class": "Book",
                "description": "A book with metadata and embeddings",
                "properties": [
                    {"name": "title", "dataType": ["text"]},
                    {"name": "author", "dataType": ["text"]},
                    {"name": "genre", "dataType": ["text"]},
                    {"name": "description", "dataType": ["text"]},
                    {"name": "isbn", "dataType": ["text"]},
                    {"name": "rating", "dataType": ["number"]},
                    {"name": "year", "dataType": ["int"]},
                    {"name": "pages", "dataType": ["int"]},
                    {"name": "language", "dataType": ["text"]},
                    {"name": "publisher", "dataType": ["text"]},
                    {"name": "cover_image", "dataType": ["text"]},
                    {"name": "price", "dataType": ["number"]},
                    {"name": "embedding", "dataType": ["vector"], "vectorizer": "text2vec-openai"},
                ],
                "vectorizer": "text2vec-openai"
            }
            
            # Create user preferences class
            user_class = {
                "class": "UserPreferences",
                "description": "User reading preferences and history",
                "properties": [
                    {"name": "user_id", "dataType": ["int"]},
                    {"name": "preferred_genres", "dataType": ["text[]"]},
                    {"name": "reading_level", "dataType": ["text"]},
                    {"name": "favorite_authors", "dataType": ["text[]"]},
                    {"name": "preferred_languages", "dataType": ["text[]"]},
                    {"name": "max_price", "dataType": ["number"]},
                    {"name": "min_rating", "dataType": ["number"]},
                    {"name": "embedding", "dataType": ["vector"], "vectorizer": "text2vec-openai"},
                ],
                "vectorizer": "text2vec-openai"
            }
            
            # Create schema
            weaviate_client.schema.create_class(book_class)
            weaviate_client.schema.create_class(user_class)
            logger.info("✅ Weaviate schema created successfully")
            
        except Exception as e:
            logger.warning(f"Schema might already exist: {e}")
    
    def create_book_embedding(self, book_data: Dict) -> List[float]:
        """Create embedding for a book"""
        text = f"{book_data.get('title', '')} {book_data.get('author', '')} {book_data.get('genre', '')} {book_data.get('description', '')}"
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    
    def create_user_embedding(self, user_preferences: Dict) -> List[float]:
        """Create embedding for user preferences"""
        text = f"{' '.join(user_preferences.get('preferred_genres', []))} {user_preferences.get('reading_level', '')} {' '.join(user_preferences.get('favorite_authors', []))}"
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    
    def enrich_book_metadata(self, book_data: Dict) -> Dict:
        """Enrich book data using DuckDuckGo if missing genre or description"""
        title = book_data.get("title", "")
        author = book_data.get("author", "")
        if not title:
            return book_data
        query = f"{title} {author} book genre description"
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        # Simple extraction: look for genre/description in snippets
        for result in results:
            snippet = result.get("body", "")
            if not book_data.get("genre") and "genre" in snippet.lower():
                # Extract genre from snippet
                genre = self.extract_genre_from_text(snippet)
                if genre:
                    book_data["genre"] = genre
            if not book_data.get("description") and len(snippet) > 40:
                book_data["description"] = snippet
            if book_data.get("genre") and book_data.get("description"):
                break
        return book_data
    
    def extract_genre_from_text(self, text: str) -> Optional[str]:
        """Extract genre from text using simple heuristics"""
        match = re.search(r"genre[:\s]+([A-Za-z, ]+)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip().split(",")[0]
        return None
    
    def store_book_in_weaviate(self, book_data: Dict):
        """Store book in Weaviate with embedding, enriching metadata if needed"""
        try:
            # Enrich metadata if missing
            if not book_data.get("genre") or not book_data.get("description"):
                book_data = self.enrich_book_metadata(book_data)
            embedding = self.create_book_embedding(book_data)
            data_object = {
                "title": book_data.get("title", ""),
                "author": book_data.get("author", ""),
                "genre": book_data.get("genre", ""),
                "description": book_data.get("description", ""),
                "isbn": book_data.get("isbn", ""),
                "rating": book_data.get("rating", 0.0),
                "year": book_data.get("year", 0),
                "pages": book_data.get("pages", 0),
                "language": book_data.get("language", ""),
                "publisher": book_data.get("publisher", ""),
                "cover_image": book_data.get("cover_image", ""),
                "price": book_data.get("price", 0.0),
                "embedding": embedding
            }
            weaviate_client.data_object.create(data_object, "Book")
            logger.info(f"✅ Stored book: {book_data.get('title')}")
        except Exception as e:
            logger.error(f"❌ Error storing book: {e}")
    
    def get_similar_books(self, book_id: str, limit: int = 5) -> List[Dict]:
        """Get similar books using vector similarity"""
        try:
            # Get the book's embedding
            book = weaviate_client.data_object.get_by_id(book_id, class_name="Book")
            if not book:
                return []
            
            # Find similar books
            result = weaviate_client.query.get("Book", [
                "title", "author", "genre", "description", "rating", "price"
            ]).with_near_vector({
                "vector": book["embedding"]
            }).with_limit(limit + 1).do()
            
            # Remove the original book from results
            similar_books = []
            for book_data in result["data"]["Get"]["Book"]:
                if book_data.get("title") != book.get("title"):
                    similar_books.append(book_data)
            
            return similar_books[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting similar books: {e}")
            return []
    
    def get_personalized_recommendations(self, user_id: int, user_preferences: Dict, limit: int = 10) -> List[Dict]:
        """Get personalized recommendations using user preferences"""
        try:
            user_embedding = self.create_user_embedding(user_preferences)
            
            # Query books based on user preferences
            result = weaviate_client.query.get("Book", [
                "title", "author", "genre", "description", "rating", "price", "year"
            ]).with_near_vector({
                "vector": user_embedding
            }).with_additional(["distance"]).with_limit(limit).do()
            
            return result["data"]["Get"]["Book"]
            
        except Exception as e:
            logger.error(f"❌ Error getting personalized recommendations: {e}")
            return []

class LangGraphRecommendationPipeline:
    """LangGraph-based recommendation pipeline"""
    
    def __init__(self):
        self.agent = BookRecommendationAgent()
        self.setup_graph()
    
    def setup_graph(self):
        """Setup LangGraph pipeline"""
        
        # Define the state
        class RecommendationState:
            def __init__(self):
                self.user_id = None
                self.user_preferences = None
                self.current_books = []
                self.recommendations = []
                self.reasoning = ""
                self.context = {}
        
        # Create the graph
        workflow = StateGraph(RecommendationState)
        
        # Add nodes
        workflow.add_node("analyze_user", self.analyze_user_node)
        workflow.add_node("generate_recommendations", self.generate_recommendations_node)
        workflow.add_node("explain_recommendations", self.explain_recommendations_node)
        
        # Add edges
        workflow.set_entry_point("analyze_user")
        workflow.add_edge("analyze_user", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "explain_recommendations")
        workflow.add_edge("explain_recommendations", END)
        
        # Compile the graph
        self.graph = workflow.compile(checkpointer=MemorySaver())
    
    def analyze_user_node(self, state):
        """Analyze user preferences and context"""
        prompt = ChatPromptTemplate.from_template("""
        Analyze the user's reading preferences and provide insights:
        
        User ID: {user_id}
        User Preferences: {user_preferences}
        Current Books: {current_books}
        
        Provide a detailed analysis of the user's reading patterns, preferences, and potential interests.
        Focus on genres, authors, themes, and reading level.
        """)
        
        chain = prompt | self.agent.llm | JsonOutputParser()
        
        analysis = chain.invoke({
            "user_id": state.user_id,
            "user_preferences": state.user_preferences,
            "current_books": state.current_books
        })
        
        state.context["analysis"] = analysis
        return state
    
    def generate_recommendations_node(self, state):
        """Generate recommendations using the agent"""
        recommendations = self.agent.get_personalized_recommendations(
            state.user_id, 
            state.user_preferences, 
            limit=10
        )
        
        state.recommendations = recommendations
        return state
    
    def explain_recommendations_node(self, state):
        """Explain the recommendations using LLM"""
        prompt = ChatPromptTemplate.from_template("""
        Based on the user analysis and recommendations, explain why these books were recommended:
        
        User Analysis: {analysis}
        Recommendations: {recommendations}
        
        Provide a detailed explanation of why each book was recommended, including:
        1. How it matches user preferences
        2. Similarity to current books
        3. Potential appeal factors
        4. Any unique aspects that might interest the user
        """)
        
        chain = prompt | self.agent.llm
        
        explanation = chain.invoke({
            "analysis": state.context.get("analysis", {}),
            "recommendations": state.recommendations
        })
        
        state.reasoning = explanation.content
        return state

class MCPServer:
    """MCP Server for book recommendations"""
    
    def __init__(self):
        self.pipeline = LangGraphRecommendationPipeline()
        self.agent = BookRecommendationAgent()
    
    async def handle_recommendation_request(self, request: Dict) -> Dict:
        """Handle recommendation requests"""
        try:
            user_id = request.get("user_id")
            user_preferences = request.get("user_preferences", {})
            current_books = request.get("current_books", [])
            
            # Run the LangGraph pipeline
            config = {"configurable": {"thread_id": f"user_{user_id}"}}
            result = await self.pipeline.graph.ainvoke({
                "user_id": user_id,
                "user_preferences": user_preferences,
                "current_books": current_books
            }, config)
            
            return {
                "status": "success",
                "recommendations": result.recommendations,
                "reasoning": result.reasoning,
                "analysis": result.context.get("analysis", {})
            }
            
        except Exception as e:
            logger.error(f"❌ Error in recommendation request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def handle_similar_books_request(self, request: Dict) -> Dict:
        """Handle similar books requests"""
        try:
            book_id = request.get("book_id")
            limit = request.get("limit", 5)
            
            similar_books = self.agent.get_similar_books(book_id, limit)
            
            return {
                "status": "success",
                "similar_books": similar_books
            }
            
        except Exception as e:
            logger.error(f"❌ Error in similar books request: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def handle_store_book_request(self, request: Dict) -> Dict:
        """Handle store book requests"""
        try:
            book_data = request.get("book_data", {})
            
            self.agent.store_book_in_weaviate(book_data)
            
            return {
                "status": "success",
                "message": f"Book '{book_data.get('title')}' stored successfully"
            }
            
        except Exception as e:
            logger.error(f"❌ Error storing book: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# FastAPI integration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Bkmrk'd MCP AI Server", version="1.0.0")

class RecommendationRequest(BaseModel):
    user_id: int
    user_preferences: Dict
    current_books: Optional[List[Dict]] = []

class SimilarBooksRequest(BaseModel):
    book_id: str
    limit: Optional[int] = 5

class StoreBookRequest(BaseModel):
    book_data: Dict

mcp_server = MCPServer()

@app.post("/recommendations")
async def get_recommendations(request: RecommendationRequest):
    """Get AI-powered book recommendations"""
    result = await mcp_server.handle_recommendation_request(request.dict())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/similar-books")
async def get_similar_books(request: SimilarBooksRequest):
    """Get similar books using vector similarity"""
    result = await mcp_server.handle_similar_books_request(request.dict())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.post("/store-book")
async def store_book(request: StoreBookRequest):
    """Store a book in the vector database"""
    result = await mcp_server.handle_store_book_request(request.dict())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Bkmrk'd MCP AI Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 