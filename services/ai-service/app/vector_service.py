#!/usr/bin/env python3
"""
Vector Service for Bkmrk'd AI System
Handles embedding generation and vector search using Weaviate
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import weaviate
from weaviate import Client
import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)

class VectorService:
    """Vector service for embedding generation and search"""
    
    def __init__(self):
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.client = Client(self.weaviate_url)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Batch processing settings
        self.batch_size = 100
        self.max_workers = 4
        
    async def initialize_schema(self):
        """Initialize Weaviate schema for books"""
        try:
            # Check if schema exists
            schema = self.client.schema.get()
            
            # Create book class if it doesn't exist
            book_class = {
                "class": "Book",
                "description": "A book with metadata and embeddings",
                "vectorizer": "text2vec-transformers",
                "moduleConfig": {
                    "text2vec-transformers": {
                        "model": "sentence-transformers/all-MiniLM-L6-v2",
                        "poolingStrategy": "masked_mean",
                        "vectorizeClassName": False
                    }
                },
                "properties": [
                    {
                        "name": "book_id",
                        "dataType": ["int"],
                        "description": "Unique book identifier"
                    },
                    {
                        "name": "title",
                        "dataType": ["text"],
                        "description": "Book title",
                        "vectorizePropertyName": True
                    },
                    {
                        "name": "author",
                        "dataType": ["text"],
                        "description": "Book author",
                        "vectorizePropertyName": True
                    },
                    {
                        "name": "description",
                        "dataType": ["text"],
                        "description": "Book description",
                        "vectorizePropertyName": True
                    },
                    {
                        "name": "genre",
                        "dataType": ["text"],
                        "description": "Book genre",
                        "vectorizePropertyName": True
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
                    },
                    {
                        "name": "year",
                        "dataType": ["int"],
                        "description": "Publication year"
                    },
                    {
                        "name": "isbn",
                        "dataType": ["text"],
                        "description": "ISBN number"
                    },
                    {
                        "name": "language",
                        "dataType": ["text"],
                        "description": "Book language"
                    },
                    {
                        "name": "publisher",
                        "dataType": ["text"],
                        "description": "Publisher"
                    },
                    {
                        "name": "pages",
                        "dataType": ["int"],
                        "description": "Number of pages"
                    }
                ]
            }
            
            # Create schema if it doesn't exist
            try:
                self.client.schema.create_class(book_class)
                logger.info("✅ Book schema created in Weaviate")
            except Exception as e:
                if "already exists" not in str(e):
                    raise e
                logger.info("✅ Book schema already exists in Weaviate")
                
        except Exception as e:
            logger.error(f"❌ Error initializing Weaviate schema: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return []
    
    def create_book_text(self, book: Dict[str, Any]) -> str:
        """Create text representation of book for embedding"""
        text_parts = [
            book.get("title", ""),
            book.get("author", ""),
            book.get("description", ""),
            book.get("genre", ""),
            str(book.get("year", "")),
            book.get("language", ""),
            book.get("publisher", "")
        ]
        return " ".join(filter(None, text_parts))
    
    async def add_book_to_vector_db(self, book: Dict[str, Any]) -> bool:
        """Add a book to the vector database"""
        try:
            # Create text representation
            book_text = self.create_book_text(book)
            
            # Generate embedding
            embedding = self.generate_embedding(book_text)
            
            if not embedding:
                return False
            
            # Prepare data object
            data_object = {
                "book_id": book.get("id"),
                "title": book.get("title", ""),
                "author": book.get("author", ""),
                "description": book.get("description", ""),
                "genre": book.get("genre", ""),
                "rating": book.get("rating", 0.0),
                "price": book.get("price", 0.0),
                "year": book.get("year", 0),
                "isbn": book.get("isbn", ""),
                "language": book.get("language", ""),
                "publisher": book.get("publisher", ""),
                "pages": book.get("pages", 0)
            }
            
            # Add to Weaviate
            self.client.data_object.create(
                data_object=data_object,
                class_name="Book"
            )
            
            logger.info(f"✅ Added book {book.get('title')} to vector database")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error adding book to vector DB: {e}")
            return False
    
    async def batch_add_books(self, books: List[Dict[str, Any]]) -> int:
        """Add multiple books to vector database in batches"""
        try:
            added_count = 0
            
            # Process in batches
            for i in range(0, len(books), self.batch_size):
                batch = books[i:i + self.batch_size]
                
                # Create tasks for batch
                tasks = [self.add_book_to_vector_db(book) for book in batch]
                
                # Execute batch
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful additions
                for result in results:
                    if isinstance(result, bool) and result:
                        added_count += 1
                
                logger.info(f"✅ Processed batch {i//self.batch_size + 1}: {len(batch)} books")
            
            logger.info(f"✅ Added {added_count} books to vector database")
            return added_count
            
        except Exception as e:
            logger.error(f"❌ Error in batch book addition: {e}")
            return 0
    
    async def search_similar_books(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar books using vector similarity"""
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            if not query_embedding:
                return []
            
            # Search in Weaviate
            response = self.client.query.get("Book", [
                "book_id", "title", "author", "description", 
                "genre", "rating", "price", "year", "isbn"
            ]).with_near_vector({
                "vector": query_embedding
            }).with_limit(limit).do()
            
            # Extract results
            results = response.get("data", {}).get("Get", {}).get("Book", [])
            
            logger.info(f"✅ Found {len(results)} similar books for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching similar books: {e}")
            return []
    
    async def search_by_text(self, text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search books by text using semantic search"""
        try:
            # Search in Weaviate using nearText
            response = self.client.query.get("Book", [
                "book_id", "title", "author", "description", 
                "genre", "rating", "price", "year", "isbn"
            ]).with_near_text({
                "concepts": [text]
            }).with_limit(limit).do()
            
            # Extract results
            results = response.get("data", {}).get("Get", {}).get("Book", [])
            
            logger.info(f"✅ Found {len(results)} books for text search: {text}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in text search: {e}")
            return []
    
    async def get_book_recommendations(self, book_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on a specific book"""
        try:
            # Get the book details
            response = self.client.query.get("Book", [
                "book_id", "title", "author", "description", 
                "genre", "rating", "price", "year", "isbn"
            ]).with_where({
                "path": ["book_id"],
                "operator": "Equal",
                "valueInt": book_id
            }).do()
            
            book = response.get("data", {}).get("Get", {}).get("Book", [])
            
            if not book:
                return []
            
            book = book[0]
            
            # Create search query from book details
            search_query = f"{book.get('title', '')} {book.get('author', '')} {book.get('genre', '')}"
            
            # Search for similar books
            similar_books = await self.search_similar_books(search_query, limit + 1)
            
            # Filter out the original book
            recommendations = [b for b in similar_books if b.get("book_id") != book_id]
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error getting book recommendations: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vector service health"""
        try:
            # Check Weaviate connection
            is_ready = self.client.is_ready()
            
            # Check schema
            schema = self.client.schema.get()
            
            return {
                "status": "healthy" if is_ready else "unhealthy",
                "weaviate_ready": is_ready,
                "schema_exists": "Book" in [cls["class"] for cls in schema.get("classes", [])],
                "embedding_model": "all-MiniLM-L6-v2"
            }
            
        except Exception as e:
            logger.error(f"❌ Vector service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Initialize vector service
vector_service = VectorService() 