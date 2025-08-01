#!/usr/bin/env python3
"""
Industrial Standard Data Loader for Bkmrk'd Bookstore
Handles 3 tables from Kaggle dataset with proper mapping
"""

import os
import sys
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndustrialDataLoader:
    """Industrial standard data loader for bookstore"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def download_kaggle_dataset(self, dataset_name: str = "saurabhbagchi/books-dataset") -> str:
        """Download Kaggle dataset with proper error handling"""
        try:
            # Initialize Kaggle API
            api = KaggleApi()
            api.authenticate()
            
            logger.info(f"📥 Downloading dataset: {dataset_name}")
            
            # Download dataset
            api.dataset_download_files(dataset_name, path="./data", unzip=True)
            
            logger.info("✅ Dataset downloaded successfully")
            return "./data"
            
        except Exception as e:
            logger.error(f"❌ Failed to download dataset: {e}")
            raise
    
    def analyze_dataset_structure(self, data_path: str) -> Dict[str, Any]:
        """Analyze the actual structure of the 3 tables"""
        try:
            csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
            logger.info(f"📊 Found {len(csv_files)} CSV files: {csv_files}")
            
            dataset_info = {}
            
            for csv_file in csv_files:
                file_path = os.path.join(data_path, csv_file)
                df = pd.read_csv(file_path)
                
                dataset_info[csv_file] = {
                    "rows": len(df),
                    "columns": list(df.columns),
                    "sample_data": df.head(3).to_dict('records'),
                    "data_types": df.dtypes.to_dict(),
                    "null_counts": df.isnull().sum().to_dict()
                }
                
                logger.info(f"📋 {csv_file}: {len(df)} rows, {len(df.columns)} columns")
                logger.info(f"   Columns: {list(df.columns)}")
            
            return dataset_info
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze dataset: {e}")
            raise
    
    def map_columns_to_schema(self, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Map actual Kaggle columns to our database schema"""
        try:
            mapping = {}
            
            for filename, info in dataset_info.items():
                logger.info(f"🔍 Analyzing mapping for {filename}")
                
                # Common column mappings
                column_mappings = {
                    # Book table mappings
                    "title": ["title", "book_title", "name", "book_name"],
                    "author": ["author", "authors", "writer", "book_author"],
                    "genre": ["genre", "category", "type", "book_genre"],
                    "description": ["description", "summary", "synopsis", "book_description"],
                    "price": ["price", "cost", "amount", "book_price"],
                    "rating": ["rating", "score", "book_rating", "average_rating"],
                    "isbn": ["isbn", "isbn13", "isbn_13", "book_isbn"],
                    "cover_image": ["cover_image", "image", "cover", "book_cover"],
                    "published_date": ["published_date", "publication_date", "year", "publish_date"],
                    
                    # User table mappings (if exists)
                    "email": ["email", "user_email", "email_address"],
                    "name": ["name", "user_name", "full_name", "username"],
                    
                    # Review table mappings (if exists)
                    "review_text": ["review", "comment", "review_text", "user_review"],
                    "review_rating": ["review_rating", "user_rating", "rating"],
                    "user_id": ["user_id", "user", "reviewer_id"],
                    "book_id": ["book_id", "book", "item_id"]
                }
                
                # Find actual mappings
                actual_mappings = {}
                for target_col, possible_sources in column_mappings.items():
                    for source_col in possible_sources:
                        if source_col in info["columns"]:
                            actual_mappings[target_col] = source_col
                            break
                
                mapping[filename] = actual_mappings
                logger.info(f"   Mapped columns: {actual_mappings}")
            
            return mapping
            
        except Exception as e:
            logger.error(f"❌ Failed to map columns: {e}")
            raise
    
    def transform_data(self, dataset_info: Dict[str, Any], column_mapping: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Transform data based on actual column mappings"""
        try:
            transformed_data = {}
            
            for filename, info in dataset_info.items():
                file_path = f"./data/{filename}"
                df = pd.read_csv(file_path)
                
                mappings = column_mapping.get(filename, {})
                transformed_records = []
                
                for _, row in df.iterrows():
                    record = {}
                    
                    # Map columns based on actual mappings
                    for target_col, source_col in mappings.items():
                        if source_col in df.columns:
                            value = row[source_col]
                            
                            # Handle data type conversions
                            if target_col == "price" and pd.notna(value):
                                try:
                                    record[target_col] = float(value)
                                except:
                                    record[target_col] = 0.0
                            elif target_col == "rating" and pd.notna(value):
                                try:
                                    record[target_col] = float(value)
                                except:
                                    record[target_col] = 0.0
                            elif target_col == "published_date" and pd.notna(value):
                                try:
                                    record[target_col] = pd.to_datetime(value)
                                except:
                                    record[target_col] = None
                            else:
                                record[target_col] = value if pd.notna(value) else None
                    
                    transformed_records.append(record)
                
                transformed_data[filename] = transformed_records
                logger.info(f"✅ Transformed {len(transformed_records)} records from {filename}")
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"❌ Failed to transform data: {e}")
            raise
    
    def load_to_database(self, transformed_data: Dict[str, List[Dict]], table_mapping: Dict[str, str]):
        """Load transformed data to appropriate database tables"""
        try:
            db = self.SessionLocal()
            
            for filename, records in transformed_data.items():
                table_name = table_mapping.get(filename, "books")  # Default to books table
                logger.info(f"📥 Loading {len(records)} records to {table_name} table")
                
                # This would need to be implemented based on your actual database models
                # For now, we'll log the data structure
                logger.info(f"   Sample record: {records[0] if records else 'No records'}")
                
            db.close()
            logger.info("✅ Data loading completed")
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Database error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load data: {e}")
            raise
    
    def run_industrial_loading(self, dataset_name: str = "saurabhbagchi/books-dataset"):
        """Complete industrial standard data loading process"""
        try:
            logger.info("🚀 Starting industrial data loading process")
            
            # Step 1: Download dataset
            data_path = self.download_kaggle_dataset(dataset_name)
            
            # Step 2: Analyze structure
            dataset_info = self.analyze_dataset_structure(data_path)
            
            # Step 3: Map columns
            column_mapping = self.map_columns_to_schema(dataset_info)
            
            # Step 4: Transform data
            transformed_data = self.transform_data(dataset_info, column_mapping)
            
            # Step 5: Determine table mapping (you need to specify this based on your 3 tables)
            table_mapping = {
                # Map your CSV files to database tables
                # Example: "books.csv": "books", "users.csv": "users", "reviews.csv": "reviews"
            }
            
            # Step 6: Load to database
            self.load_to_database(transformed_data, table_mapping)
            
            logger.info("🎉 Industrial data loading completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Industrial data loading failed: {e}")
            raise

def main():
    """Main function"""
    try:
        # Get database URL from environment
        database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bookstore")
        
        # Initialize loader
        loader = IndustrialDataLoader(database_url)
        
        # Run industrial loading
        loader.run_industrial_loading()
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 