#!/usr/bin/env python3
"""
Kaggle Data Loader for Bkmrk'd
Loads book data from the Kaggle dataset: jealousleopard/goodreadsbooks
Uses Kaggle API for direct dataset access
"""

import os
import sys
import pandas as pd
import requests
import zipfile
import tempfile
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from main import Book, Base

# Ensure Kaggle credentials are set for both local and cloud
KAGGLE_USERNAME = os.environ.get("KAGGLE_USERNAME")
KAGGLE_KEY = os.environ.get("KAGGLE_KEY")
if not KAGGLE_USERNAME or not KAGGLE_KEY:
    print("❌ Kaggle credentials not set. Please set KAGGLE_USERNAME and KAGGLE_KEY in your environment.")
    sys.exit(1)

def download_kaggle_dataset():
    """Download the Kaggle dataset using Kaggle API"""
    try:
        print("📚 Downloading Kaggle dataset: jealousleopard/goodreadsbooks")
        
        # Kaggle API endpoint
        api_url = "https://www.kaggle.com/api/v1/datasets/download/jealousleopard/goodreadsbooks"
        
        # Set up authentication
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        # Download dataset
        response = requests.get(
            api_url,
            auth=(KAGGLE_USERNAME, KAGGLE_KEY),
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to download dataset: {response.status_code}")
            return None
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        # Extract zip file
        extract_path = tempfile.mkdtemp()
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Clean up zip file
        os.unlink(tmp_file_path)
        
        print(f"✅ Dataset downloaded and extracted to: {extract_path}")
        return extract_path
        
    except Exception as e:
        print(f"❌ Error downloading Kaggle dataset: {e}")
        return None

def load_kaggle_dataset():
    """Load the Kaggle dataset"""
    try:
        # Download the dataset
        path = download_kaggle_dataset()
        if not path:
            return None
        
        # Load the CSV file
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError("No CSV files found in dataset")
        
        # Load the first CSV file (assuming it's the main dataset)
        csv_path = os.path.join(path, csv_files[0])
        df = pd.read_csv(csv_path)
        
        print(f"✅ Loaded {len(df)} books from dataset")
        print(f"📊 Dataset columns: {list(df.columns)}")
        print(f"📊 Sample data:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading Kaggle dataset: {e}")
        return None

def transform_data(df):
    """Transform the Kaggle data to match our database schema"""
    try:
        # Map columns to our schema
        transformed_data = []
        
        for _, row in df.iterrows():
            book_data = {
                "title": row.get('title', 'Unknown Title'),
                "author": row.get('authors', 'Unknown Author'),
                "year": row.get('publication_date', None),
                "genre": row.get('genre', 'Unknown'),
                "description": row.get('description', ''),
                "isbn": row.get('isbn', ''),
                "isbn13": row.get('isbn13', ''),
                "rating": row.get('average_rating', 0.0),
                "pages": row.get('num_pages', 0),
                "language": row.get('language_code', 'eng'),
                "publisher": row.get('publisher', 'Unknown'),
                "cover_image": row.get('cover_image', ''),
                "price": row.get('price', 0.0),
                "ratings_count": row.get('ratings_count', 0),
                "text_reviews_count": row.get('text_reviews_count', 0)
            }
            
            # Clean up data
            if pd.isna(book_data["year"]):
                book_data["year"] = None
            if pd.isna(book_data["rating"]):
                book_data["rating"] = 0.0
            if pd.isna(book_data["pages"]):
                book_data["pages"] = 0
            if pd.isna(book_data["price"]):
                book_data["price"] = 0.0
            if pd.isna(book_data["ratings_count"]):
                book_data["ratings_count"] = 0
            if pd.isna(book_data["text_reviews_count"]):
                book_data["text_reviews_count"] = 0
            
            transformed_data.append(book_data)
        
        print(f"✅ Transformed {len(transformed_data)} books")
        return transformed_data
        
    except Exception as e:
        print(f"❌ Error transforming data: {e}")
        return []

def load_to_database(books_data):
    """Load books data into the database"""
    try:
        # Database connection
        DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/bookstore")
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Load books
        loaded_count = 0
        skipped_count = 0
        
        for book_data in books_data:
            # Check if book already exists (by ISBN or title+author)
            existing_book = db.query(Book).filter(
                (Book.isbn == book_data["isbn"]) if book_data["isbn"] else False
            ).first()
            
            if existing_book:
                skipped_count += 1
                continue
            
            # Create new book
            new_book = Book(**book_data)
            db.add(new_book)
            loaded_count += 1
            
            # Commit in batches
            if loaded_count % 100 == 0:
                db.commit()
                print(f"✅ Loaded {loaded_count} books...")
        
        # Final commit
        db.commit()
        db.close()
        
        print(f"✅ Database loading completed:")
        print(f"   - Loaded: {loaded_count} books")
        print(f"   - Skipped: {skipped_count} books (already exist)")
        
    except Exception as e:
        print(f"❌ Error loading to database: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def main():
    """Main function to run the data loading process"""
    try:
        print("🚀 Starting Kaggle data loading process...")
        
        # Load dataset
        df = load_kaggle_dataset()
        if df is None:
            print("❌ Failed to load dataset")
            return
        
        # Transform data
        books_data = transform_data(df)
        if not books_data:
            print("❌ Failed to transform data")
            return
        
        # Load to database
        load_to_database(books_data)
        
        print("✅ Data loading process completed successfully!")
        
    except Exception as e:
        print(f"❌ Data loading process failed: {e}")

if __name__ == "__main__":
    main() 