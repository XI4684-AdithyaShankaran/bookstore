#!/usr/bin/env python3
"""
Kaggle Data Loader for Bkmrk'd Bookstore
Loads books dataset from Kaggle into PostgreSQL database
"""

import os
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import kaggle
from typing import List, Dict, Any
import time

logger = logging.getLogger(__name__)

class KaggleDataLoader:
    """Load Kaggle dataset into PostgreSQL database"""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db")
        self.kaggle_username = os.getenv("KAGGLE_USERNAME")
        self.kaggle_key = os.getenv("KAGGLE_KEY")
        self.dataset_id = os.getenv("KAGGLE_DATASET_ID", "saurabhbagchi/books-dataset")
        self.dataset_version = os.getenv("KAGGLE_DATASET_VERSION", "1")
        
        # Initialize database connection
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"KaggleDataLoader initialized with dataset: {self.dataset_id}")
    
    def setup_kaggle_credentials(self):
        """Setup Kaggle API credentials"""
        try:
            if not self.kaggle_username or not self.kaggle_key:
                raise ValueError("KAGGLE_USERNAME and KAGGLE_KEY environment variables are required")
            
            # Create .kaggle directory and credentials file
            kaggle_dir = os.path.expanduser("~/.kaggle")
            os.makedirs(kaggle_dir, exist_ok=True)
            
            credentials_content = f"""username: {self.kaggle_username}
key: {self.kaggle_key}"""
            
            with open(os.path.join(kaggle_dir, "kaggle.json"), "w") as f:
                f.write(credentials_content)
            
            # Set proper permissions
            os.chmod(os.path.join(kaggle_dir, "kaggle.json"), 0o600)
            
            logger.info("Kaggle credentials configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up Kaggle credentials: {e}")
            raise
    
    def download_dataset(self) -> str:
        """Download dataset from Kaggle"""
        try:
            logger.info(f"Downloading dataset: {self.dataset_id}")
            
            # Download the dataset
            kaggle.api.dataset_download_files(
                self.dataset_id,
                path="./temp_data",
                unzip=True
            )
            
            logger.info("Dataset downloaded successfully")
            return "./temp_data"
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            raise
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            with self.engine.connect() as conn:
                # Create books table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS books (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        author VARCHAR(200),
                        description TEXT,
                        genre VARCHAR(100),
                        rating DECIMAL(3,2) DEFAULT 0.0,
                        price DECIMAL(10,2) DEFAULT 0.0,
                        publication_date DATE,
                        isbn VARCHAR(20),
                        language VARCHAR(50),
                        pages INTEGER,
                        publisher VARCHAR(200),
                        cover_image VARCHAR(500),
                        active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create users table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(200) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255),
                        full_name VARCHAR(200),
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create ratings table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ratings (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        book_id INTEGER REFERENCES books(id),
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        review TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, book_id)
                    )
                """))
                
                # Create user_books table (for reading history)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_books (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        book_id INTEGER REFERENCES books(id),
                        status VARCHAR(50) DEFAULT 'read', -- read, reading, want_to_read
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, book_id)
                    )
                """))
                
                # Create indexes for performance
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_rating ON books(rating)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_ratings_user_book ON ratings(user_id, book_id)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_user_books_user_book ON user_books(user_id, book_id)"))
                
                conn.commit()
                
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def load_books_data(self, data_path: str):
        """Load books data from CSV into database"""
        try:
            # Read books CSV
            books_file = os.path.join(data_path, "books.csv")
            if not os.path.exists(books_file):
                raise FileNotFoundError(f"Books file not found: {books_file}")
            
            logger.info("Loading books data...")
            books_df = pd.read_csv(books_file)
            
            # Clean and prepare data
            books_df = self._clean_books_data(books_df)
            
            # Load into database
            with self.SessionLocal() as session:
                # Clear existing data
                session.execute(text("DELETE FROM books"))
                
                # Insert new data
                for _, row in books_df.iterrows():
                    book_data = {
                        "title": row.get("title", ""),
                        "author": row.get("author", ""),
                        "description": row.get("description", ""),
                        "genre": row.get("genre", ""),
                        "rating": float(row.get("rating", 0)),
                        "price": float(row.get("price", 0)),
                        "publication_date": pd.to_datetime(row.get("publication_date")).date() if pd.notna(row.get("publication_date")) else None,
                        "isbn": str(row.get("isbn", "")),
                        "language": row.get("language", "English"),
                        "pages": int(row.get("pages", 0)) if pd.notna(row.get("pages")) else None,
                        "publisher": row.get("publisher", "")
                    }
                    
                    session.execute(text("""
                        INSERT INTO books (title, author, description, genre, rating, price, 
                                         publication_date, isbn, language, pages, publisher)
                        VALUES (:title, :author, :description, :genre, :rating, :price,
                                :publication_date, :isbn, :language, :pages, :publisher)
                    """), book_data)
                
                session.commit()
            
            logger.info(f"Loaded {len(books_df)} books into database")
            
        except Exception as e:
            logger.error(f"Error loading books data: {e}")
            raise
    
    def load_users_data(self, data_path: str):
        """Load users data from CSV into database"""
        try:
            # Read users CSV
            users_file = os.path.join(data_path, "users.csv")
            if not os.path.exists(users_file):
                logger.warning(f"Users file not found: {users_file}")
                return
            
            logger.info("Loading users data...")
            users_df = pd.read_csv(users_file)
            
            # Clean and prepare data
            users_df = self._clean_users_data(users_df)
            
            # Load into database
            with self.SessionLocal() as session:
                # Clear existing data
                session.execute(text("DELETE FROM users"))
                
                # Insert new data
                for _, row in users_df.iterrows():
                    user_data = {
                        "username": f"user_{row.get('id', '')}",
                        "email": f"user_{row.get('id', '')}@example.com",
                        "full_name": f"User {row.get('id', '')}"
                    }
                    
                    session.execute(text("""
                        INSERT INTO users (username, email, full_name)
                        VALUES (:username, :email, :full_name)
                    """), user_data)
                
                session.commit()
            
            logger.info(f"Loaded {len(users_df)} users into database")
            
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
            raise
    
    def load_ratings_data(self, data_path: str):
        """Load ratings data from CSV into database"""
        try:
            # Read ratings CSV
            ratings_file = os.path.join(data_path, "ratings.csv")
            if not os.path.exists(ratings_file):
                logger.warning(f"Ratings file not found: {ratings_file}")
                return
            
            logger.info("Loading ratings data...")
            ratings_df = pd.read_csv(ratings_file)
            
            # Clean and prepare data
            ratings_df = self._clean_ratings_data(ratings_df)
            
            # Load into database
            with self.SessionLocal() as session:
                # Clear existing data
                session.execute(text("DELETE FROM ratings"))
                
                # Insert new data in batches
                batch_size = 1000
                for i in range(0, len(ratings_df), batch_size):
                    batch = ratings_df.iloc[i:i+batch_size]
                    
                    for _, row in batch.iterrows():
                        rating_data = {
                            "user_id": int(row.get("user_id", 0)),
                            "book_id": int(row.get("book_id", 0)),
                            "rating": int(row.get("rating", 0))
                        }
                        
                        session.execute(text("""
                            INSERT INTO ratings (user_id, book_id, rating)
                            VALUES (:user_id, :book_id, :rating)
                            ON CONFLICT (user_id, book_id) DO UPDATE SET
                            rating = EXCLUDED.rating
                        """), rating_data)
                    
                    session.commit()
                    logger.info(f"Processed ratings batch {i//batch_size + 1}")
            
            logger.info(f"Loaded {len(ratings_df)} ratings into database")
            
        except Exception as e:
            logger.error(f"Error loading ratings data: {e}")
            raise
    
    def _clean_books_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare books data"""
        # Remove duplicates
        df = df.drop_duplicates(subset=['title', 'author'])
        
        # Handle missing values
        df['title'] = df['title'].fillna('Unknown Title')
        df['author'] = df['author'].fillna('Unknown Author')
        df['genre'] = df['genre'].fillna('General')
        df['rating'] = df['rating'].fillna(0.0)
        df['price'] = df['price'].fillna(0.0)
        
        # Clean text fields
        df['title'] = df['title'].str.strip()
        df['author'] = df['author'].str.strip()
        df['genre'] = df['genre'].str.strip()
        
        # Limit text lengths
        df['title'] = df['title'].str[:500]
        df['author'] = df['author'].str[:200]
        df['genre'] = df['genre'].str[:100]
        
        return df
    
    def _clean_users_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare users data"""
        # Remove duplicates
        df = df.drop_duplicates(subset=['id'])
        
        # Handle missing values
        df['id'] = df['id'].fillna(0)
        
        return df
    
    def _clean_ratings_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare ratings data"""
        # Remove duplicates
        df = df.drop_duplicates(subset=['user_id', 'book_id'])
        
        # Handle missing values
        df['user_id'] = df['user_id'].fillna(0)
        df['book_id'] = df['book_id'].fillna(0)
        df['rating'] = df['rating'].fillna(0)
        
        # Filter valid ratings
        df = df[(df['rating'] >= 1) & (df['rating'] <= 5)]
        
        return df
    
    def run_full_load(self):
        """Run complete data loading process"""
        try:
            logger.info("Starting Kaggle data loading process...")
            
            # Setup Kaggle credentials
            self.setup_kaggle_credentials()
            
            # Create database tables
            self.create_tables()
            
            # Download dataset
            data_path = self.download_dataset()
            
            # Load data
            self.load_books_data(data_path)
            self.load_users_data(data_path)
            self.load_ratings_data(data_path)
            
            # Cleanup
            import shutil
            if os.path.exists(data_path):
                shutil.rmtree(data_path)
            
            logger.info("Data loading process completed successfully!")
            
        except Exception as e:
            logger.error(f"Data loading process failed: {e}")
            raise

def main():
    """Main function to run the data loader"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    loader = KaggleDataLoader()
    loader.run_full_load()

if __name__ == "__main__":
    main() 