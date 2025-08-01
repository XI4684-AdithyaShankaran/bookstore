#!/usr/bin/env python3
"""
RAGAS Analytics Library for Bkmrk'd Recommendation System
Provides analytics methods for evaluating recommendation performance
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
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
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGASAnalytics:
    """RAGAS analytics for recommendation system evaluation"""
    
    def __init__(self):
        # Configuration from environment variables
        self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Dynamic metrics configuration
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_relevancy,
            context_recall,
            answer_correctness,
            answer_similarity
        ]
        
        # Performance configuration
        self.batch_size = int(os.getenv('ANALYTICS_BATCH_SIZE', '50'))
        self.cache_size = int(os.getenv('ANALYTICS_CACHE_SIZE', '100'))
        self.timeout = int(os.getenv('ANALYTICS_TIMEOUT', '60'))
        
        # Thresholds from environment
        self.faithfulness_threshold = float(os.getenv('FAITHFULNESS_THRESHOLD', '0.7'))
        self.relevancy_threshold = float(os.getenv('RELEVANCY_THRESHOLD', '0.6'))
        self.recall_threshold = float(os.getenv('RECALL_THRESHOLD', '0.5'))
        self.diversity_threshold = float(os.getenv('DIVERSITY_THRESHOLD', '0.3'))
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.6'))
        
        logger.info(f"✅ RAGAS Analytics initialized with model: {self.embedding_model_name}")
    
    def create_evaluation_dataset(self, recommendations_data: List[Dict]) -> Dataset:
        """Create evaluation dataset from recommendation data"""
        try:
            # Transform recommendation data into RAGAS format
            eval_data = []
            
            for rec_data in recommendations_data:
                # Extract components for evaluation
                question = rec_data.get("user_query", "")
                context = rec_data.get("context", [])  # List of relevant books
                answer = rec_data.get("recommendation_explanation", "")
                ground_truth = rec_data.get("ground_truth", "")
                
                eval_data.append({
                    "question": question,
                    "contexts": context,
                    "answer": answer,
                    "ground_truth": ground_truth
                })
            
            # Create dataset
            dataset = Dataset.from_list(eval_data)
            logger.info(f"✅ Created evaluation dataset with {len(eval_data)} samples")
            return dataset
            
        except Exception as e:
            logger.error(f"❌ Error creating evaluation dataset: {e}")
            return None
    
    def evaluate_recommendations(self, dataset: Dataset) -> Dict[str, float]:
        """Evaluate recommendations using RAGAS metrics"""
        try:
            logger.info("🔍 Starting RAGAS evaluation...")
            
            # Run evaluation
            results = evaluate(dataset, self.metrics)
            
            # Extract scores
            scores = {}
            for metric_name, score in results.items():
                scores[metric_name] = float(score)
            
            logger.info("✅ RAGAS evaluation completed")
            return scores
            
        except Exception as e:
            logger.error(f"❌ Error in RAGAS evaluation: {e}")
            return {}
    
    def analyze_recommendation_quality(self, recommendations: List[Dict]) -> Dict[str, Any]:
        """Analyze recommendation quality metrics"""
        try:
            analysis = {
                "total_recommendations": len(recommendations),
                "average_rating": 0.0,
                "genre_diversity": 0.0,
                "author_diversity": 0.0,
                "price_range": {"min": 0.0, "max": 0.0, "avg": 0.0},
                "year_range": {"min": 0, "max": 0, "avg": 0},
                "popularity_score": 0.0
            }
            
            if not recommendations:
                return analysis
            
            # Calculate metrics
            ratings = [rec.get("rating", 0.0) for rec in recommendations]
            prices = [rec.get("price", 0.0) for rec in recommendations]
            years = [rec.get("year", 0) for rec in recommendations]
            genres = [rec.get("genre", "") for rec in recommendations]
            authors = [rec.get("author", "") for rec in recommendations]
            
            # Basic statistics
            analysis["average_rating"] = np.mean(ratings) if ratings else 0.0
            analysis["genre_diversity"] = len(set(genres)) / len(genres) if genres else 0.0
            analysis["author_diversity"] = len(set(authors)) / len(authors) if authors else 0.0
            
            # Price analysis
            if prices:
                analysis["price_range"]["min"] = min(prices)
                analysis["price_range"]["max"] = max(prices)
                analysis["price_range"]["avg"] = np.mean(prices)
            
            # Year analysis
            if years:
                analysis["year_range"]["min"] = min(years)
                analysis["year_range"]["max"] = max(years)
                analysis["year_range"]["avg"] = int(np.mean(years))
            
            # Popularity score (based on ratings and reviews)
            popularity_scores = []
            for rec in recommendations:
                rating = rec.get("rating", 0.0)
                pages = rec.get("pages", 0)
                year = rec.get("year", 2024)
                
                # Dynamic popularity formula based on environment variables
                rating_weight = float(os.getenv('RATING_WEIGHT', '0.6'))
                pages_weight = float(os.getenv('PAGES_WEIGHT', '0.2'))
                year_weight = float(os.getenv('YEAR_WEIGHT', '0.2'))
                
                popularity = (rating * rating_weight) + (min(pages, 1000) / 1000 * pages_weight) + (max(0, 2024 - year) / 100 * year_weight)
                popularity_scores.append(popularity)
            
            analysis["popularity_score"] = np.mean(popularity_scores) if popularity_scores else 0.0
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing recommendation quality: {e}")
            return {}
    
    def calculate_embedding_similarity(self, user_preferences: Dict, recommendations: List[Dict]) -> float:
        """Calculate embedding similarity between user preferences and recommendations"""
        try:
            # Create user preference embedding
            user_text = f"{' '.join(user_preferences.get('preferred_genres', []))} {user_preferences.get('reading_level', '')} {' '.join(user_preferences.get('favorite_authors', []))}"
            user_embedding = self.embedding_model.encode(user_text)
            
            # Create recommendation embeddings
            rec_embeddings = []
            for rec in recommendations:
                rec_text = f"{rec.get('title', '')} {rec.get('author', '')} {rec.get('genre', '')} {rec.get('description', '')}"
                rec_embedding = self.embedding_model.encode(rec_text)
                rec_embeddings.append(rec_embedding)
            
            if not rec_embeddings:
                return 0.0
            
            # Calculate similarities
            similarities = []
            for rec_embedding in rec_embeddings:
                similarity = cosine_similarity([user_embedding], [rec_embedding])[0][0]
                similarities.append(similarity)
            
            return np.mean(similarities)
            
        except Exception as e:
            logger.error(f"❌ Error calculating embedding similarity: {e}")
            return 0.0
    
    def generate_analytics_report(self, evaluation_results: Dict, quality_analysis: Dict, similarity_score: float) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "evaluation_metrics": evaluation_results,
                "quality_analysis": quality_analysis,
                "similarity_score": similarity_score,
                "overall_score": 0.0,
                "recommendations": []
            }
            
            # Calculate overall score
            scores = []
            if evaluation_results:
                scores.extend(evaluation_results.values())
            if quality_analysis.get("average_rating"):
                scores.append(quality_analysis["average_rating"] / 5.0)  # Normalize to 0-1
            if similarity_score:
                scores.append(similarity_score)
            
            if scores:
                report["overall_score"] = np.mean(scores)
            
            # Generate recommendations based on thresholds
            recommendations = []
            
            if report["overall_score"] < 0.5:
                recommendations.append("Consider improving recommendation diversity")
                recommendations.append("Enhance user preference understanding")
                recommendations.append("Optimize embedding similarity calculations")
            
            if quality_analysis.get("genre_diversity", 0) < self.diversity_threshold:
                recommendations.append("Increase genre diversity in recommendations")
            
            if quality_analysis.get("author_diversity", 0) < self.diversity_threshold:
                recommendations.append("Include more diverse authors in recommendations")
            
            if similarity_score < self.similarity_threshold:
                recommendations.append("Improve user preference to recommendation matching")
            
            # Add dynamic recommendations based on evaluation metrics
            if evaluation_results.get("faithfulness", 0) < self.faithfulness_threshold:
                recommendations.append("Improve AI model training to better align with source context")
            
            if evaluation_results.get("answer_relevancy", 0) < self.relevancy_threshold:
                recommendations.append("Enhance user preference modeling and recommendation algorithms")
            
            if evaluation_results.get("context_recall", 0) < self.recall_threshold:
                recommendations.append("Expand context utilization in recommendation engine")
            
            report["recommendations"] = recommendations
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating analytics report: {e}")
            return {}
    
    def save_analytics_report(self, report: Dict, filename: str = None) -> str:
        """Save analytics report to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"analytics_report_{timestamp}.json"
            
            # Get report directory from environment
            report_dir = os.getenv('ANALYTICS_REPORT_DIR', 'analytics')
            filepath = f"{report_dir}/{filename}"
            os.makedirs(report_dir, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"✅ Analytics report saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error saving analytics report: {e}")
            return ""

# Export the analytics class for use by other services
__all__ = ['RAGASAnalytics'] 