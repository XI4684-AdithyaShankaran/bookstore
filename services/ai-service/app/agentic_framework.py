#!/usr/bin/env python3
"""
Agentic Framework for Bkmrk'd AI System
Uses LangGraph for multi-agent orchestration with tools and search capabilities
"""

import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import httpx
import os
import json

logger = logging.getLogger(__name__)

# Initialize LLM with proper configuration
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",
    temperature=0.7,
    top_p=0.9,
    max_tokens=2048,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Define tools for the agents
@tool
async def search_books(query: str) -> List[Dict[str, Any]]:
    """Search for books using the internal database"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('API_SERVER_URL', 'http://localhost:8000')}/books",
                params={"search": query, "limit": 10}
            )
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        logger.error(f"Error searching books: {e}")
        return []

@tool
async def search_web(query: str) -> str:
    """Search the web for book information using DuckDuckGo"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": f"{query} book information",
                    "format": "json",
                    "no_html": "1",
                    "skip_disambig": "1"
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("Abstract", "No information found")
            return "Search failed"
    except Exception as e:
        logger.error(f"Error searching web: {e}")
        return "Search failed"

@tool
async def get_book_details(book_id: int) -> Dict[str, Any]:
    """Get detailed information about a specific book"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('API_SERVER_URL', 'http://localhost:8000')}/books/{book_id}"
            )
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        logger.error(f"Error getting book details: {e}")
        return {}

@tool
async def search_vector_db(query: str) -> List[Dict[str, Any]]:
    """Search the vector database for similar books"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{os.getenv('WEAVIATE_URL', 'http://localhost:8080')}/v1/graphql",
                json={
                    "query": """
                    {
                        Get {
                            Book(
                                nearText: {
                                    concepts: ["%s"]
                                }
                                limit: 10
                            ) {
                                book_id
                                title
                                author
                                genre
                                rating
                                price
                            }
                        }
                    }
                    """ % query
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("Get", {}).get("Book", [])
            return []
    except Exception as e:
        logger.error(f"Error searching vector DB: {e}")
        return []

# Agent state management
class AgentState:
    def __init__(self):
        self.user_query = ""
        self.search_results = []
        self.recommendations = []
        self.enhanced_recommendations = []
        self.current_step = "search"
        self.error = None

def create_agentic_workflow():
    """Create the agentic workflow using LangGraph"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("search_agent", search_agent_node)
    workflow.add_node("recommendation_agent", recommendation_agent_node)
    workflow.add_node("enhancement_agent", enhancement_agent_node)
    workflow.add_node("tool_executor", ToolNode([search_books, search_web, get_book_details, search_vector_db]))
    
    # Define edges
    workflow.set_entry_point("search_agent")
    workflow.add_edge("search_agent", "recommendation_agent")
    workflow.add_edge("recommendation_agent", "enhancement_agent")
    workflow.add_edge("enhancement_agent", END)
    
    return workflow.compile()

async def search_agent_node(state: AgentState) -> AgentState:
    """Search agent node - finds relevant books"""
    try:
        # Use tools to search for books
        search_results = await search_books(state.user_query)
        web_results = await search_web(state.user_query)
        
        state.search_results = search_results
        state.current_step = "recommendation"
        
        logger.info(f"Search agent found {len(search_results)} books")
        return state
        
    except Exception as e:
        state.error = str(e)
        logger.error(f"Search agent error: {e}")
        return state

async def recommendation_agent_node(state: AgentState) -> AgentState:
    """Recommendation agent node - generates recommendations"""
    try:
        # Build context from search results
        context = f"User Query: {state.user_query}\n"
        context += f"Found Books: {len(state.search_results)}\n"
        
        if state.search_results:
            context += "Book Titles: " + ", ".join([book.get("title", "") for book in state.search_results[:5]])
        
        # Generate recommendations using LLM
        prompt = f"""
        Based on the user query and search results, provide book recommendations.
        
        User Query: {state.user_query}
        Search Results: {context}
        
        Provide recommendations in JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Book Title",
                    "author": "Author Name",
                    "genre": "Genre",
                    "reasoning": "Why this book is recommended",
                    "confidence": 0.95
                }}
            ]
        }}
        """
        
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        recommendations = parse_recommendations(response.content)
        
        state.recommendations = recommendations.get("recommendations", [])
        state.current_step = "enhancement"
        
        logger.info(f"Recommendation agent generated {len(state.recommendations)} recommendations")
        return state
        
    except Exception as e:
        state.error = str(e)
        logger.error(f"Recommendation agent error: {e}")
        return state

async def enhancement_agent_node(state: AgentState) -> AgentState:
    """Enhancement agent node - adds additional information"""
    try:
        if not state.recommendations:
            state.enhanced_recommendations = []
            return state
        
        # Enhance each recommendation with additional information
        enhanced = []
        for rec in state.recommendations:
            # Get additional details from vector DB
            vector_results = await search_vector_db(rec.get("title", ""))
            
            # Enhance with pricing and availability info
            enhancement = await enhance_recommendations([rec], "Enhance with pricing and availability")
            
            if enhancement:
                enhanced.extend(enhancement)
            else:
                enhanced.append(rec)
        
        state.enhanced_recommendations = enhanced
        state.current_step = "complete"
        
        logger.info(f"Enhancement agent processed {len(enhanced)} recommendations")
        return state
        
    except Exception as e:
        state.error = str(e)
        logger.error(f"Enhancement agent error: {e}")
        return state

def parse_recommendations(content: str) -> Dict[str, Any]:
    """Parse recommendations from LLM response"""
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
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Error parsing recommendations: {e}")
        return {"recommendations": []}

async def enhance_recommendations(recommendations: List[Dict[str, Any]], enhancements: str) -> List[Dict[str, Any]]:
    """Enhance recommendations with additional information"""
    try:
        enhanced = []
        for rec in recommendations:
            enhanced_rec = rec.copy()
            
            # Extract pricing information
            pricing_info = extract_pricing_info(enhancements)
            if pricing_info:
                enhanced_rec.update(pricing_info)
            
            # Extract availability information
            availability_info = extract_availability_info(enhancements)
            if availability_info:
                enhanced_rec.update(availability_info)
            
            # Extract series information
            series_info = extract_series_info(enhancements)
            if series_info:
                enhanced_rec.update(series_info)
            
            # Extract review information
            review_info = extract_review_info(enhancements)
            if review_info:
                enhanced_rec.update(review_info)
            
            enhanced.append(enhanced_rec)
        
        return enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing recommendations: {e}")
        return recommendations

def extract_pricing_info(text: str) -> Dict[str, Any]:
    """Extract pricing information from text"""
    try:
        price_match = re.search(r'\$(\d+\.?\d*)', text)
        if price_match:
            return {"price": float(price_match.group(1))}
        return {}
    except Exception:
        return {}

def extract_availability_info(text: str) -> Dict[str, Any]:
    """Extract availability information from text"""
    try:
        if "in stock" in text.lower():
            return {"availability": "in_stock"}
        elif "out of stock" in text.lower():
            return {"availability": "out_of_stock"}
        return {"availability": "unknown"}
    except Exception:
        return {}

def extract_series_info(text: str) -> Dict[str, Any]:
    """Extract series information from text"""
    try:
        series_match = re.search(r'series[:\s]+([^,\n]+)', text, re.IGNORECASE)
        if series_match:
            return {"series": series_match.group(1).strip()}
        return {}
    except Exception:
        return {}

def extract_review_info(text: str) -> Dict[str, Any]:
    """Extract review information from text"""
    try:
        rating_match = re.search(r'(\d+\.?\d*)\s*stars?', text, re.IGNORECASE)
        if rating_match:
            return {"rating": float(rating_match.group(1))}
        return {}
    except Exception:
        return {}

async def run_agentic_recommendation(user_query: str) -> Dict[str, Any]:
    """Run the complete agentic recommendation workflow"""
    try:
        # Create workflow
        workflow = create_agentic_workflow()
        
        # Initialize state
        initial_state = AgentState()
        initial_state.user_query = user_query
        
        # Run workflow
        result = await workflow.ainvoke(initial_state)
        
        return {
            "success": True,
            "recommendations": result.enhanced_recommendations,
            "search_results": result.search_results,
            "error": result.error
        }
        
    except Exception as e:
        logger.error(f"Error running agentic recommendation: {e}")
        return {
            "success": False,
            "error": str(e),
            "recommendations": []
        } 