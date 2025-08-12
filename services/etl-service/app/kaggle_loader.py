#!/usr/bin/env python3
"""
Kaggle Data Loader for Bkmrk'd Bookstore
Loads books dataset from Kaggle into PostgreSQL database
"""

import os
import importlib
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
# import kaggle  # Moved this import inside methods
from typing import List, Dict, Any, cast
import time
from pathlib import Path

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
    
    def _resolve_books_data_dir(self) -> str:
        """Resolve absolute path to repo-level books_data directory by walking up parents"""
        current_path = Path(__file__).resolve()
        for parent in [current_path] + list(current_path.parents):
            candidate = parent / "books_data"
            if candidate.exists() and candidate.is_dir():
                return str(candidate)
        # Fallback: assume repo root three levels up from this file
        fallback = Path(__file__).resolve().parents[3] / "books_data"
        return str(fallback)
    
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
    
    def _resolve_data_path(self) -> str:
        """Use existing books_data if present, otherwise optionally download via Kaggle into books_data."""
        local_dir = self._resolve_books_data_dir()
        books_file = os.path.join(local_dir, "books.csv")
        users_file = os.path.join(local_dir, "users.csv")
        ratings_file = os.path.join(local_dir, "ratings.csv")

        if os.path.exists(books_file) and os.path.exists(users_file) and os.path.exists(ratings_file):
            logger.info(f"Using local dataset at {local_dir}")
            return local_dir

        # Fall back to Kaggle download only if credentials are provided
        if self.kaggle_username and self.kaggle_key:
            return self.download_dataset(local_dir)

        raise FileNotFoundError(
            "books_data folder with books.csv, users.csv, and ratings.csv not found and Kaggle credentials not provided."
        )

    def download_dataset(self, target_dir: str) -> str:
        """Download dataset from Kaggle into target_dir/books_data"""
        try:
            # Set up credentials first
            self.setup_kaggle_credentials()
            
            # Import kaggle after credentials are set up (dynamic to avoid static analyzer warning)
            try:
                kaggle = cast(Any, importlib.import_module("kaggle"))
            except Exception as exc:
                raise ImportError(
                    "The 'kaggle' package is required for dataset downloads. Install it with: "
                    "python -m pip install -r services/etl-service/requirements.txt"
                ) from exc
            
            Path(target_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Downloading dataset: {self.dataset_id} into {target_dir}")
            
            # Download the dataset
            kaggle.api.dataset_download_files(
                self.dataset_id,
                path=target_dir,
                unzip=True
            )
            
            logger.info("Dataset downloaded successfully")
            return target_dir
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            raise
    
    def create_tables(self):
        """Create database tables if they don't exist (aligned with backend models)."""
        try:
            with self.engine.connect() as conn:
                # Create books table (matches backend columns)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS books (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        author VARCHAR(200) NOT NULL,
                        description TEXT,
                        genre VARCHAR(100),
                        price DECIMAL(10,2) DEFAULT 0.0,
                        rating DECIMAL(3,2) DEFAULT 0.0,
                        image_url VARCHAR(500),
                        isbn VARCHAR(20) UNIQUE,
                        publication_date DATE,
                        page_count INTEGER,
                        language VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))

                # Create users table (matches backend columns)
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(200) UNIQUE NOT NULL,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        full_name VARCHAR(200),
                        is_active BOOLEAN DEFAULT true,
                        is_superuser BOOLEAN DEFAULT false,
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

                # Useful indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS idx_books_author ON books(author)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_books_isbn ON books(isbn)"))
                conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_ratings_user_book ON ratings(user_id, book_id)"))

                conn.commit()

            logger.info("Database tables ensured (books, users, ratings)")

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def reset_database(self):
        """Delete existing data for a full clean load (safely, only known tables)."""
        try:
            with self.engine.connect() as conn:
                existing_tables = {
                    row[0] for row in conn.execute(
                        text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")
                    )
                }
                targets = [t for t in ["ratings", "books", "users"] if t in existing_tables]
                if targets:
                    # TRUNCATE is faster and CASCADE clears dependents where needed
                    stmt = "TRUNCATE TABLE " + ", ".join(targets) + " RESTART IDENTITY CASCADE"
                    conn.execute(text(stmt))
                conn.commit()
            logger.info(f"Database reset completed for tables: {', '.join(targets) if targets else 'none'}")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            raise
    
    def load_books_data(self, data_path: str):
        """Load books data from CSV into database"""
        try:
            # Read books CSV
            books_file = os.path.join(data_path, "books.csv")
            if not os.path.exists(books_file):
                raise FileNotFoundError(f"Books file not found: {books_file}")
            
            logger.info("Loading books data...")
            
            # Read CSV manually to handle quoted fields with semicolons
            import csv
            
            books_data = []
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(books_file, 'r', encoding=encoding) as file:
                        reader = csv.DictReader(file, delimiter=';', quotechar='"')
                        books_data = list(reader)
                        logger.info(f"Successfully read books.csv with {encoding} encoding")
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding}: {e}")
                    continue
            
            if not books_data:
                raise ValueError("Could not read books.csv with any supported encoding")
            
            # Convert to DataFrame for easier processing
            books_df = pd.DataFrame(books_data)
            
            # Clean and prepare data
            books_df = self._clean_books_data(books_df)
            
            # Load into database
            with self.SessionLocal() as session:
                # Upsert books to avoid duplicates
                total = len(books_df)
                processed = 0
                for _, row in books_df.iterrows():
                    # Handle publication date safely
                    publication_date = None
                    try:
                        year = row.get("Year-Of-Publication")
                        if year and str(year).isdigit() and int(year) > 1900 and int(year) <= 2024:
                            publication_date = pd.to_datetime(f"{year}-01-01").date()
                    except:
                        publication_date = None
                    
                    book_data = {
                        "title": row.get("Book-Title", ""),
                        "author": row.get("Book-Author", ""),
                        "description": "",  # Not available in this dataset
                        "genre": "General",  # Not available in this dataset
                        "price": 0.0,  # Not available in this dataset
                        "rating": 0.0,  # Not available in this dataset
                        "image_url": row.get("Image-URL-L", ""),
                        "isbn": str(row.get("ISBN", "")),
                        "publication_date": publication_date,
                        "page_count": None,  # Not available in this dataset
                        "language": "English"  # Default
                    }

                    # Skip if ISBN missing
                    if not book_data["isbn"]:
                        continue

                    session.execute(text("""
                        INSERT INTO books (title, author, description, genre, price, rating,
                                           image_url, isbn, publication_date, page_count, language)
                        VALUES (:title, :author, :description, :genre, :price, :rating,
                                :image_url, :isbn, :publication_date, :page_count, :language)
                        ON CONFLICT (isbn) DO UPDATE SET
                            title = EXCLUDED.title,
                            author = EXCLUDED.author,
                            description = EXCLUDED.description,
                            genre = EXCLUDED.genre,
                            price = EXCLUDED.price,
                            rating = EXCLUDED.rating,
                            image_url = EXCLUDED.image_url,
                            publication_date = EXCLUDED.publication_date,
                            page_count = EXCLUDED.page_count,
                            language = EXCLUDED.language
                    """), book_data)
                    processed += 1
                    if processed % 5000 == 0:
                        logger.info(f"Processed books: {processed}/{total}")
                
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
            
            # Read CSV manually to handle quoted fields with semicolons
            import csv
            
            users_data = []
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(users_file, 'r', encoding=encoding) as file:
                        reader = csv.DictReader(file, delimiter=';', quotechar='"')
                        users_data = list(reader)
                        logger.info(f"Successfully read users.csv with {encoding} encoding")
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding}: {e}")
                    continue
            
            if not users_data:
                logger.warning("Could not read users.csv with any supported encoding")
                return
            
            # Convert to DataFrame for easier processing
            users_df = pd.DataFrame(users_data)
            
            # Clean and prepare data
            users_df = self._clean_users_data(users_df)
            
            # Load into database
            with self.SessionLocal() as session:
                # Upsert users by unique email
                total = len(users_df)
                processed = 0
                for _, row in users_df.iterrows():
                    user_data = {
                        "username": f"user_{row.get('User-ID', '')}",
                        "email": f"user_{row.get('User-ID', '')}@example.com",
                        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJQhK8e",  # Default password: password123
                        "full_name": f"User {row.get('User-ID', '')}",
                        "is_active": True,
                        "is_superuser": False
                    }
                    
                    session.execute(text("""
                        INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser)
                        VALUES (:username, :email, :hashed_password, :full_name, :is_active, :is_superuser)
                        ON CONFLICT (email) DO UPDATE SET
                            username = EXCLUDED.username,
                            full_name = EXCLUDED.full_name,
                            is_active = EXCLUDED.is_active,
                            is_superuser = EXCLUDED.is_superuser
                    """), user_data)
                    processed += 1
                    if processed % 5000 == 0:
                        logger.info(f"Processed users: {processed}/{total}")
                
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
            
            # Read CSV manually to handle quoted fields with semicolons
            import csv
            
            ratings_data = []
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(ratings_file, 'r', encoding=encoding) as file:
                        reader = csv.DictReader(file, delimiter=';', quotechar='"')
                        ratings_data = list(reader)
                        logger.info(f"Successfully read ratings.csv with {encoding} encoding")
                        break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding}: {e}")
                    continue
            
            if not ratings_data:
                logger.warning("Could not read ratings.csv with any supported encoding")
                return
            
            # Convert to DataFrame for easier processing
            ratings_df = pd.DataFrame(ratings_data)
            
            # Clean and prepare data
            ratings_df = self._clean_ratings_data(ratings_df)
            
            # Create ISBN to book_id mapping and user email->id mapping
            with self.SessionLocal() as session:
                result = session.execute(text("SELECT id, isbn FROM books"))
                isbn_to_book_id = {str(row[1]): int(row[0]) for row in result if row[1]}
                user_rows = session.execute(text("SELECT id, email FROM users"))
                email_to_user_id = {str(row[1]): int(row[0]) for row in user_rows if row[1]}
            
            # Load into database
            with self.SessionLocal() as session:
                # Upsert ratings in batches
                batch_size = 1000
                valid_ratings = 0
                
                for i in range(0, len(ratings_df), batch_size):
                    batch = ratings_df.iloc[i:i+batch_size]
                    
                    for _, row in batch.iterrows():
                        isbn = str(row.get("ISBN", ""))
                        if isbn in isbn_to_book_id:
                            # Map Kaggle User-ID to our user.id via email
                            kaggle_uid = str(int(row.get("User-ID", 0)))
                            user_email = f"user_{kaggle_uid}@example.com"
                            user_id_val = email_to_user_id.get(user_email)
                            if not user_id_val:
                                continue
                            rating_data = {
                                "user_id": user_id_val,
                                "book_id": isbn_to_book_id[isbn],
                                "rating": float(row.get("Book-Rating", 0))
                            }
                            session.execute(text("""
                                INSERT INTO ratings (user_id, book_id, rating)
                                VALUES (:user_id, :book_id, :rating)
                                ON CONFLICT (user_id, book_id) DO UPDATE SET
                                    rating = EXCLUDED.rating
                            """), rating_data)
                            valid_ratings += 1
                    
                    session.commit()
                    logger.info(f"Processed ratings batch {i//batch_size + 1}")
            
            logger.info(f"Loaded {valid_ratings} valid ratings into database")
            
        except Exception as e:
            logger.error(f"Error loading ratings data: {e}")
            raise
    
    def _clean_books_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare books data"""
        # Remove duplicates and ensure a copy to avoid SettingWithCopyWarning
        df = df.drop_duplicates(subset=['Book-Title', 'Book-Author']).copy()
        
        # Handle missing values
        df['Book-Title'] = df['Book-Title'].fillna('Unknown Title')
        df['Book-Author'] = df['Book-Author'].fillna('Unknown Author')
        df['Image-URL-L'] = df['Image-URL-L'].fillna('')
        
        # Clean text fields
        df['Book-Title'] = df['Book-Title'].str.strip()
        df['Book-Author'] = df['Book-Author'].str.strip()
        
        # Limit text lengths
        df['Book-Title'] = df['Book-Title'].str[:500]
        df['Book-Author'] = df['Book-Author'].str[:200]
        
        return df
    
    def _clean_users_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare users data"""
        # Remove duplicates and ensure a copy to avoid SettingWithCopyWarning
        df = df.drop_duplicates(subset=['User-ID']).copy()
        
        # Handle missing values
        df['User-ID'] = df['User-ID'].fillna(0)
        
        return df
    
    def _clean_ratings_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare ratings data"""
        # Remove duplicates and ensure a copy to avoid SettingWithCopyWarning
        df = df.drop_duplicates(subset=['User-ID', 'ISBN']).copy()

        # Normalize types and handle missing values
        df['User-ID'] = pd.to_numeric(df['User-ID'], errors='coerce').fillna(0).astype(int)
        df['ISBN'] = df['ISBN'].fillna('').astype(str).str.strip()
        # Ratings often come as strings; coerce to numeric and drop invalids
        df['Book-Rating'] = pd.to_numeric(df['Book-Rating'], errors='coerce')

        # Filter valid ratings 1..5 and return a copy
        df = df[df['Book-Rating'].between(1, 5, inclusive='both')].copy()

        return df
    
    def run_full_load(self):
        """Run complete data loading process"""
        try:
            logger.info("Starting Kaggle data loading process...")
            # Ensure required tables exist before any operations
            self.create_tables()
            # Resolve data path (prefer local books_data)
            data_path = self._resolve_data_path()
            # Reset if explicitly requested (one-time full reload)
            if os.getenv("ETL_FULL_RESET", "").lower() in ("1", "true", "yes"):
                self.reset_database()
            
            # Load data
            self.load_books_data(data_path)
            self.load_users_data(data_path)
            self.load_ratings_data(data_path)
            # Do not delete books_data; keep local CSVs for reuse
            
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