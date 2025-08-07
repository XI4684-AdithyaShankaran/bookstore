#!/usr/bin/env python3
"""
Kaggle Data Loader for Bkmrk'd
Loads book data from the Kaggle dataset: saurabhbagchi/books-dataset
Uses the downloaded dataset files
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend service to the path for database models
sys.path.append('/Users/apple/workspace/bookstore/services/backend-service')

from app.database.database import SessionLocal
from app.database.models import Book, User, Rating

def load_csv_with_encoding(file_path, sep=';'):
    """Load CSV file with automatic encoding detection"""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            return pd.read_csv(file_path, sep=sep, quotechar='"', encoding=encoding, on_bad_lines='skip')
        except Exception as e:
            print(f"Failed with encoding {encoding}: {e}")
            continue
    
    raise Exception(f"Could not read {file_path} with any encoding")

def load_kaggle_dataset():
    """Load the Kaggle dataset from downloaded files"""
    try:
        print("📖 Loading books data...")
        books_df = load_csv_with_encoding('/Users/apple/workspace/bookstore/books_data/books.csv')
        
        print("👥 Loading users data...")
        users_df = load_csv_with_encoding('/Users/apple/workspace/bookstore/books_data/users.csv')
        
        print("⭐ Loading ratings data...")
        ratings_df = load_csv_with_encoding('/Users/apple/workspace/bookstore/books_data/ratings.csv')
        
        print(f"📊 Dataset loaded:")
        print(f"   Books: {len(books_df)} records")
        print(f"   Users: {len(users_df)} records") 
        print(f"   Ratings: {len(ratings_df)} records")
        
        return books_df, users_df, ratings_df
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return None, None, None

def clean_data(books_df, users_df, ratings_df):
    """Clean and prepare the data"""
    print("🧹 Cleaning data...")
    
    # Clean books data
    books_df = books_df.dropna(subset=['Book-Title', 'Book-Author'])
    books_df['Year-Of-Publication'] = pd.to_numeric(books_df['Year-Of-Publication'], errors='coerce')
    books_df = books_df[books_df['Year-Of-Publication'].notna()]
    books_df = books_df[books_df['Year-Of-Publication'] > 1900]
    books_df = books_df[books_df['Year-Of-Publication'] <= 2024]
    
    # Clean users data
    users_df = users_df.dropna(subset=['User-ID'])
    users_df['Age'] = pd.to_numeric(users_df['Age'], errors='coerce')
    users_df = users_df[users_df['Age'].isna() | (users_df['Age'] >= 13)]
    
    # Clean ratings data
    ratings_df = ratings_df.dropna(subset=['User-ID', 'ISBN', 'Book-Rating'])
    ratings_df['Book-Rating'] = pd.to_numeric(ratings_df['Book-Rating'], errors='coerce')
    ratings_df = ratings_df[ratings_df['Book-Rating'] >= 0]
    
    print(f"✅ Data cleaned:")
    print(f"   Books: {len(books_df)} records")
    print(f"   Users: {len(users_df)} records")
    print(f"   Ratings: {len(ratings_df)} records")
    
    return books_df, users_df, ratings_df

def load_to_database(books_df, users_df, ratings_df, max_books=500, max_users=50, max_ratings=200):
    """Load data into the database"""
    try:
        db = SessionLocal()
        
        # Import books
        print("📚 Importing books...")
        books_to_import = books_df.head(max_books)
        
        for _, row in books_to_import.iterrows():
            try:
                # Generate a random price between $9.99 and $29.99
                price = round(np.random.uniform(9.99, 29.99), 2)
                
                # Generate a random rating between 3.5 and 5.0
                rating = round(np.random.uniform(3.5, 5.0), 1)
                
                # Use the medium image URL or fallback
                image_url = row['Image-URL-M'] if pd.notna(row['Image-URL-M']) else 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400'
                
                # Clean title and author
                title = str(row['Book-Title'])[:200] if pd.notna(row['Book-Title']) else "Unknown Title"
                author = str(row['Book-Author'])[:100] if pd.notna(row['Book-Author']) else "Unknown Author"
                
                book = Book(
                    title=title,
                    author=author,
                    description=f"A fascinating book by {author} published in {int(row['Year-Of-Publication'])}.",
                    genre="Fiction",  # Default genre
                    price=price,
                    rating=rating,
                    image_url=image_url,
                    isbn=str(row['ISBN']),
                    publication_date=datetime(int(row['Year-Of-Publication']), 1, 1),
                    language="English"
                )
                
                db.add(book)
                
            except Exception as e:
                print(f"⚠️  Skipping book {row.get('Book-Title', 'Unknown')}: {e}")
                continue
        
        db.commit()
        print(f"✅ Successfully imported {len(books_to_import)} books!")
        
        # Import users
        print("👥 Importing users...")
        users_to_import = users_df.head(max_users)
        
        for _, row in users_to_import.iterrows():
            try:
                username = f"user_{int(row['User-ID'])}"
                email = f"user_{int(row['User-ID'])}@example.com"
                
                user = User(
                    email=email,
                    username=username,
                    hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iQeO",  # Default password: "password"
                    full_name=f"User {int(row['User-ID'])}",
                    is_active=True
                )
                
                db.add(user)
                
            except Exception as e:
                print(f"⚠️  Skipping user {row.get('User-ID', 'Unknown')}: {e}")
                continue
        
        db.commit()
        print(f"✅ Successfully imported {len(users_to_import)} users!")
        
        # Import ratings
        print("⭐ Importing ratings...")
        ratings_to_import = ratings_df.head(max_ratings)
        
        for _, row in ratings_to_import.iterrows():
            try:
                # Check if user and book exist
                user_exists = db.query(User).filter(User.id == int(row['User-ID'])).first()
                book_exists = db.query(Book).filter(Book.isbn == str(row['ISBN'])).first()
                
                if user_exists and book_exists:
                    rating = Rating(
                        user_id=int(row['User-ID']),
                        book_id=book_exists.id,
                        rating=float(row['Book-Rating']),
                        review=f"User rating for {book_exists.title}"
                    )
                    db.add(rating)
                
            except Exception as e:
                print(f"⚠️  Skipping rating: {e}")
                continue
        
        db.commit()
        print(f"✅ Successfully imported ratings!")
        
        # Update book ratings based on actual ratings
        print("📊 Updating book ratings...")
        for book in db.query(Book).all():
            book_ratings = db.query(Rating).filter(Rating.book_id == book.id).all()
            if book_ratings:
                avg_rating = sum(r.rating for r in book_ratings) / len(book_ratings)
                book.rating = round(avg_rating, 1)
        
        db.commit()
        print("✅ Book ratings updated!")
        
        # Final statistics
        total_books = db.query(Book).count()
        total_users = db.query(User).count()
        total_ratings = db.query(Rating).count()
        
        print(f"\n🎉 Import completed successfully!")
        print(f"📚 Total books in database: {total_books}")
        print(f"👥 Total users in database: {total_users}")
        print(f"⭐ Total ratings in database: {total_ratings}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error during import: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()

def main():
    """Main function to run the data loading process"""
    try:
        print("🚀 Starting Kaggle data loading process...")
        
        # Load dataset
        books_df, users_df, ratings_df = load_kaggle_dataset()
        if books_df is None:
            print("❌ Failed to load dataset")
            return
        
        # Clean data
        books_df, users_df, ratings_df = clean_data(books_df, users_df, ratings_df)
        
        # Load to database
        load_to_database(books_df, users_df, ratings_df)
        
        print("✅ Data loading process completed successfully!")
        
    except Exception as e:
        print(f"❌ Data loading process failed: {e}")

if __name__ == "__main__":
    main() 