#!/usr/bin/env python3
"""
Analytics Server for Bkmrk'd - RAGAS Evaluation and Analytics
Provides evaluation metrics for AI recommendations and system performance
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_relevancy,
    context_recall,
    answer_correctness,
    answer_similarity
)
from datasets import Dataset
from ragas_analytics import RAGASAnalytics
import os
from datetime import datetime, timedelta
from functools import lru_cache
import gc

# Configure logging with optimized settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analytics_server.log', maxBytes=1024*1024, backupCount=3)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Analytics Server - RAGAS Evaluation")

class RecommendationEvaluationRequest(BaseModel):
    recommendations: List[Dict[str, Any]]
    user_feedback: Optional[Dict[str, Any]] = None
    context: Optional[str] = None

class EvaluationResponse(BaseModel):
    metrics: Dict[str, float]
    insights: List[str]
    recommendations: List[str]
    timestamp: str

class SystemMetricsRequest(BaseModel):
    time_period: str = "24h"  # 24h, 7d, 30d
    metrics: List[str] = ["recommendation_accuracy", "user_satisfaction", "system_performance"]

class SystemMetricsResponse(BaseModel):
    metrics: Dict[str, Any]
    trends: Dict[str, List[float]]
    alerts: List[str]

# Cache for expensive evaluations
evaluation_cache = {}

# Initialize RAGAS analytics
ragas_analytics = RAGASAnalytics()

@app.on_event("startup")
async def startup_event():
    """Initialize the analytics server on startup"""
    try:
        logger.info("✅ Analytics server initialized")
        logger.info("✅ RAGAS evaluation framework ready")
        logger.info("✅ RAGAS analytics library loaded")
        
        # Start cache cleanup task
        asyncio.create_task(cache_cleanup_task())
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize analytics server: {e}")
        raise

async def cache_cleanup_task():
    """Periodic cache cleanup to prevent memory leaks"""
    while True:
        await asyncio.sleep(300)  # Cleanup every 5 minutes
        cleanup_expired_cache()
        gc.collect()

def cleanup_expired_cache():
    """Remove expired cache entries"""
    current_time = datetime.utcnow()
    expired_keys = []
    
    for key, (data, timestamp) in evaluation_cache.items():
        if (current_time - timestamp).total_seconds() > 1800:  # 30 minutes TTL
            expired_keys.append(key)
    
    for key in expired_keys:
        del evaluation_cache[key]
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

@lru_cache(maxsize=100)
def get_cached_evaluation(recommendations_hash: str) -> Optional[Dict]:
    """Get cached evaluation results"""
    if recommendations_hash in evaluation_cache:
        return evaluation_cache[recommendations_hash][0]
    return None

def cache_evaluation(recommendations_hash: str, result: Dict):
    """Cache evaluation results"""
    evaluation_cache[recommendations_hash] = (result, datetime.utcnow())
    
    # Limit cache size
    if len(evaluation_cache) > 200:
        # Remove oldest entries
        oldest_key = min(evaluation_cache.keys(), key=lambda k: evaluation_cache[k][1])
        del evaluation_cache[oldest_key]

@app.post("/evaluate-recommendations", response_model=EvaluationResponse)
async def evaluate_recommendations(request: RecommendationEvaluationRequest):
    """Evaluate AI recommendations using RAGAS metrics with caching"""
    try:
        # Create cache key from recommendations
        recommendations_str = json.dumps(request.recommendations, sort_keys=True)
        recommendations_hash = str(hash(recommendations_str))
        
        # Check cache first
        cached_result = get_cached_evaluation(recommendations_hash)
        if cached_result:
            logger.info("✅ Returning cached evaluation result")
            return EvaluationResponse(**cached_result)
        
        # Use RAGAS analytics library for evaluation
        dataset = ragas_analytics.create_evaluation_dataset(request.recommendations)
        if not dataset:
            raise HTTPException(status_code=400, detail="Failed to create evaluation dataset")
        
        # Run RAGAS evaluation using the library with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(ragas_analytics.evaluate_recommendations, dataset),
                timeout=60  # 60 second timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Evaluation timeout")
        
        # Extract metrics with error handling
        metrics = results  # RAGAS analytics library already returns the correct format
        
        # Generate insights with memory cleanup
        insights = generate_insights(metrics, request)
        
        # Generate recommendations
        recommendations = generate_recommendations(metrics, insights)
        
        result = EvaluationResponse(
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
        # Cache the result
        cache_evaluation(recommendations_hash, result.dict())
        
        # Force garbage collection
        gc.collect()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to evaluate recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Note: prepare_evaluation_data function removed - now handled by RAGAS analytics library

def generate_insights(metrics: Dict[str, float], request: RecommendationEvaluationRequest) -> List[str]:
    """Generate insights from evaluation metrics with optimized logic"""
    insights = []
    
    # Use optimized threshold checks
    thresholds = {
        "faithfulness": {"low": 0.7, "high": 0.9},
        "answer_relevancy": {"low": 0.6, "high": 0.8},
        "context_recall": {"low": 0.5, "high": 0.8}
    }
    
    for metric, threshold in thresholds.items():
        value = metrics.get(metric, 0.0)
        if value < threshold["low"]:
            insights.append(f"{metric.replace('_', ' ').title()} needs improvement")
        elif value > threshold["high"]:
            insights.append(f"Excellent {metric.replace('_', ' ')}")
    
    # Overall assessment with optimized calculation
    valid_metrics = [v for v in metrics.values() if v > 0]
    if valid_metrics:
        avg_score = sum(valid_metrics) / len(valid_metrics)
        if avg_score < 0.6:
            insights.append("Overall recommendation quality needs improvement")
        elif avg_score > 0.8:
            insights.append("Excellent overall recommendation quality")
    
    return insights

def generate_recommendations(metrics: Dict[str, float], insights: List[str]) -> List[str]:
    """Generate improvement recommendations with optimized logic"""
    recommendations = []
    
    # Use dictionary for efficient threshold checking
    improvement_areas = {
        "faithfulness": "Improve AI model training to better align with source context",
        "answer_relevancy": "Enhance user preference modeling and recommendation algorithms",
        "context_recall": "Expand context utilization in recommendation engine",
        "answer_correctness": "Improve fact-checking and validation of book information"
    }
    
    for metric, recommendation in improvement_areas.items():
        if metrics.get(metric, 0.0) < 0.7:
            recommendations.append(recommendation)
    
    # Add general recommendations
    general_recommendations = [
        "Consider A/B testing different recommendation strategies",
        "Implement user feedback loops for continuous improvement",
        "Monitor recommendation diversity to avoid filter bubbles"
    ]
    recommendations.extend(general_recommendations)
    
    return recommendations

@app.get("/system-metrics", response_model=SystemMetricsResponse)
async def get_system_metrics(request: SystemMetricsRequest):
    """Get system-wide performance metrics with caching"""
    try:
        # Calculate time period
        end_time = datetime.now()
        if request.time_period == "24h":
            start_time = end_time - timedelta(hours=24)
        elif request.time_period == "7d":
            start_time = end_time - timedelta(days=7)
        elif request.time_period == "30d":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(hours=24)
        
        # Get metrics from database (simplified)
        metrics = await get_metrics_from_database(start_time, end_time)
        
        # Calculate trends with optimized processing
        trends = calculate_trends(metrics, request.time_period)
        
        # Generate alerts
        alerts = generate_alerts(metrics, trends)
        
        return SystemMetricsResponse(
            metrics=metrics,
            trends=trends,
            alerts=alerts
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_metrics_from_database(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Get metrics from database with optimized querying"""
    # In a real implementation, this would query the database with connection pooling
    return {
        "total_recommendations": 1250,
        "successful_recommendations": 1100,
        "user_satisfaction_score": 4.2,
        "average_response_time": 0.8,
        "system_uptime": 99.8,
        "active_users": 450,
        "recommendation_accuracy": 0.85,
        "diversity_score": 0.72
    }

def calculate_trends(metrics: Dict[str, Any], time_period: str) -> Dict[str, List[float]]:
    """Calculate trends for metrics with optimized processing"""
    # Simplified trend calculation with memory optimization
    base_trends = {
        "recommendation_accuracy": [0.82, 0.84, 0.85, 0.86, 0.85],
        "user_satisfaction": [4.0, 4.1, 4.2, 4.3, 4.2],
        "response_time": [1.2, 1.0, 0.9, 0.8, 0.8]
    }
    
    # Adjust trends based on time period
    if time_period == "7d":
        # Extend trends for weekly view
        for key in base_trends:
            base_trends[key] = base_trends[key] * 2
    
    return base_trends

def generate_alerts(metrics: Dict[str, Any], trends: Dict[str, List[float]]) -> List[str]:
    """Generate system alerts based on metrics with optimized logic"""
    alerts = []
    
    # Use dictionary for efficient threshold checking
    alert_thresholds = {
        "user_satisfaction_score": {"min": 4.0, "message": "⚠️ User satisfaction below threshold"},
        "average_response_time": {"max": 1.0, "message": "⚠️ Response time above acceptable limit"},
        "system_uptime": {"min": 99.5, "message": "⚠️ System uptime below target"}
    }
    
    for metric, threshold in alert_thresholds.items():
        value = metrics.get(metric, 0)
        if "min" in threshold and value < threshold["min"]:
            alerts.append(threshold["message"])
        elif "max" in threshold and value > threshold["max"]:
            alerts.append(threshold["message"])
    
    # Trend-based alerts with optimized logic
    if "recommendation_accuracy" in trends and len(trends["recommendation_accuracy"]) >= 2:
        current = trends["recommendation_accuracy"][-1]
        previous = trends["recommendation_accuracy"][-2]
        if current < previous:
            alerts.append("📉 Recommendation accuracy declining")
    
    return alerts

@app.get("/health")
async def health_check():
    """Health check endpoint with memory status"""
    try:
        # Get memory usage for monitoring
        import psutil
        memory_info = psutil.virtual_memory()
        
        return {
            "status": "healthy",
            "service": "analytics-server",
            "timestamp": datetime.now().isoformat(),
            "memory_usage": f"{memory_info.percent}%",
            "cache_size": len(evaluation_cache)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 