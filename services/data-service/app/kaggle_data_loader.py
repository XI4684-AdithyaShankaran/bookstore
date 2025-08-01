#!/usr/bin/env python3
"""
Kaggle Data Loader for Bkmrk'd
Loads book data from the Kaggle dataset: saurabhbagchi/books-dataset
"""

import os
import sys
import pandas as pd
import kagglehub
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from main import Book, Base

# Ensure Kaggle credentials are set for both local and cloud
KAGGLE_USERNAME = os.environ.get("KAGGLE_USERNAME")
KAGGLE_KEY = os.environ.get("KAGGLE_KEY")
if not KAGGLE_USERNAME or not KAGGLE_KEY:
    print("❌ Kaggle credentials not set. Please set KAGGLE_USERNAME and KAGGLE_KEY in your environment.")
    sys.exit(1)
os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
os.environ["KAGGLE_KEY"] = KAGGLE_KEY

def load_kaggle_dataset():
    """Load the Kaggle dataset"""
    try:
        print("📚 Loading Kaggle dataset: saurabhbagchi/books-dataset")
        
        # Download the dataset
        path = kagglehub.dataset_download("saurabhbagchi/books-dataset")
        print(f"✅ Dataset downloaded to: {path}")
        
        # Load the CSV file
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError("No CSV files found in dataset")
        
        # Load the first CSV file (assuming it's the main dataset)
        csv_path = os.path.join(path, csv_files[0])
        df = pd.read_csv(csv_path)
        
        print(f"✅ Loaded {len(df)} books from dataset")
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
                "author": row.get('author', 'Unknown Author'),
                "year": row.get('year', None),
                "genre": row.get('genre', 'Unknown'),
                "description": row.get('description', ''),
                "isbn": row.get('isbn', ''),
                "rating": row.get('rating', 0.0),
                "pages": row.get('pages', 0),
                "language": row.get('language', 'English'),
                "publisher": row.get('publisher', 'Unknown'),
                "cover_image": row.get('cover_image', ''),
                "price": row.get('price', 0.0)
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
            
            if not existing_book and book_data["isbn"]:
                # Also check by title and author
                existing_book = db.query(Book).filter(
                    (Book.title == book_data["title"]) &
                    (Book.author == book_data["author"])
                ).first()
            
            if not existing_book:
                book = Book(**book_data)
                db.add(book)
                loaded_count += 1
            else:
                skipped_count += 1
        
        db.commit()
        db.close()
        
        print(f"✅ Loaded {loaded_count} new books to database")
        print(f"⏭️  Skipped {skipped_count} existing books")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading to database: {e}")
        return False

def main():
    """Main function to load Kaggle data"""
    print("🚀 Starting Kaggle data loader for Bkmrk'd")
    
    # Load dataset
    df = load_kaggle_dataset()
    if df is None:
        print("❌ Failed to load dataset")
        sys.exit(1)
    
    # Transform data
    books_data = transform_data(df)
    if not books_data:
        print("❌ Failed to transform data")
        sys.exit(1)
    
    # Load to database
    success = load_to_database(books_data)
    if not success:
        print("❌ Failed to load data to database")
        sys.exit(1)
    
    print("🎉 Kaggle data loading completed successfully!")

if __name__ == "__main__":
    main() 