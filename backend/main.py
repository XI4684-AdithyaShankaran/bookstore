# main.py

import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from datetime import timedelta

# Log rotation setup
LOG_DIR = os.environ.get("LOG_DIR", "/logs")
LOG_FILE = os.path.join(LOG_DIR, "backend_logs.txt")
os.makedirs(LOG_DIR, exist_ok=True)
handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
logging.basicConfig(level=logging.INFO, handlers=[handler], format='%(asctime)s %(levelname)s %(name)s %(message)s')

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Optional
import redis
import json
import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Import our separated modules
from app import models, schemas
from app.services.book_service import BookService
from app.services.user_service import UserService
from app.services.bookshelf_service import BookshelfService
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os

# JWT Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = UserService(db).get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception
    return user

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@host:port/dbname")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Check if we're in development mode without external services
DEV_MODE = os.environ.get("DEV_MODE", "false").lower() == "true"

if DEV_MODE:
    # Use SQLite for development when PostgreSQL is not available
    DATABASE_URL = "sqlite:///./dev.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
models.Base.metadata.create_all(bind=engine)

# Redis connection - make it optional for development
try:
    redis_client = redis.from_url(REDIS_URL)
except:
    if DEV_MODE:
        redis_client = None
    else:
        raise

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)

# Recommendation engine
class RecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        self.book_vectors = None
        self.book_ids = None

    def load_books_data(self, db):
        books = db.query(models.Book).all()
        if not books:
            return
        
        # Create text descriptions for vectorization
        book_texts = []
        self.book_ids = []
        
        for book in books:
            text = f"{book.title} {book.author} {book.genre or ''} {book.description or ''}"
            book_texts.append(text)
            self.book_ids.append(book.id)
        
        # Vectorize the text
        self.book_vectors = self.vectorizer.fit_transform(book_texts)

    def get_recommendations(self, book_id, n_recommendations=5):
        if self.book_vectors is None or book_id not in self.book_ids:
            return []
        
        book_idx = self.book_ids.index(book_id)
        book_vector = self.book_vectors[book_idx]
        
        # Calculate similarities
        similarities = cosine_similarity(book_vector, self.book_vectors).flatten()
        
        # Get top similar books (excluding the book itself)
        similar_indices = similarities.argsort()[-n_recommendations-1:-1][::-1]
        
        return [self.book_ids[i] for i in similar_indices]

    def get_user_recommendations(self, user_id, db, n_recommendations=10):
        # Simple implementation - get books from user's bookshelves and recommend similar ones
        user_bookshelves = BookshelfService(db).get_user_bookshelves(user_id)
        if not user_bookshelves:
            return []
        
        # Get all books from user's bookshelves
        user_book_ids = set()
        for bookshelf in user_bookshelves:
            # This would need a more complex query to get books from bookshelves
            pass
        
        if not user_book_ids:
            return []
        
        # Get recommendations based on user's books
        all_recommendations = []
        for book_id in list(user_book_ids)[:3]:  # Limit to 3 books to avoid too many recommendations
            recommendations = self.get_recommendations(book_id, n_recommendations // 3)
            all_recommendations.extend(recommendations)
        
        return list(set(all_recommendations))[:n_recommendations]

# Initialize recommendation engine
recommendation_engine = RecommendationEngine()

# FastAPI app
app = FastAPI(title="Bkmrk'd API", version="1.0.0")

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Development
        "http://localhost:3001",  # Alternative dev port
        "http://127.0.0.1:3000",  # Local IP
        "http://127.0.0.1:3001",  # Local IP alternative
        "*",  # Allow all origins in development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted Host Middleware (Security) - More permissive for no domain
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "*",  # Allow all hosts in development (remove in production)
    ]
)

# Authentication endpoints
@app.post("/token", response_model=schemas.Token)
@limiter.limit("5/minute")  # Rate limit login attempts
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    user = UserService(db).get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.UserSchema)
@limiter.limit("3/minute")  # Rate limit registration
def register_user(
    request: Request,
    user: schemas.UserCreate, 
    db = Depends(get_db)
):
    # Check if user already exists
    if UserService(db).get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if UserService(db).get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(user.password)
    return UserService(db).create_user(user, hashed_password)

# Book endpoints
@app.get("/books", response_model=schemas.SearchResponse)
@limiter.limit("100/minute")  # Rate limit search requests
def get_books(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    genre: Optional[str] = None,
    db = Depends(get_db)
):
    result = BookService(db).get_books(skip=skip, limit=limit, search=search, genre=genre)
    return schemas.SearchResponse(**result)

@app.get("/books/{book_id}", response_model=schemas.BookSchema)
@limiter.limit("200/minute")
def get_book(
    request: Request,
    book_id: int, 
    db = Depends(get_db)
):
    book = BookService(db).get_book_by_id(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.get("/books/{book_id}/recommendations")
@limiter.limit("50/minute")
def get_book_recommendations(
    request: Request,
    book_id: int, 
    db = Depends(get_db)
):
    # Load books data for recommendation engine
    recommendation_engine.load_books_data(db)
    
    # Get recommendations
    recommended_book_ids = recommendation_engine.get_recommendations(book_id)
    
    # Get the actual book objects
    recommended_books = []
    for rec_id in recommended_book_ids:
        book = BookService(db).get_book_by_id(rec_id)
        if book:
            recommended_books.append(book)
    
    return recommended_books

@app.get("/users/{user_id}/recommendations")
@limiter.limit("30/minute")
def get_user_recommendations(
    request: Request,
    user_id: int,
    current_user: schemas.UserSchema = Depends(get_current_user),
    db = Depends(get_db)
):
    # Load books data for recommendation engine
    recommendation_engine.load_books_data(db)
    
    # Get recommendations
    recommended_book_ids = recommendation_engine.get_user_recommendations(user_id, db)
    
    # Get the actual book objects
    recommended_books = []
    for rec_id in recommended_book_ids:
        book = BookService(db).get_book_by_id(rec_id)
        if book:
            recommended_books.append(book)
    
    return recommended_books

# Bookshelf endpoints
@app.post("/bookshelves")
@limiter.limit("20/minute")
def create_bookshelf(
    request: Request,
    name: str,
    description: Optional[str] = None,
    is_public: bool = False,
    current_user: schemas.UserSchema = Depends(get_current_user),
    db = Depends(get_db)
):
    return BookshelfService(db).create_bookshelf(current_user.id, name, description, is_public)

@app.get("/bookshelves")
@limiter.limit("50/minute")
def get_user_bookshelves(
    request: Request,
    current_user: schemas.UserSchema = Depends(get_current_user),
    db = Depends(get_db)
):
    return BookshelfService(db).get_user_bookshelves(current_user.id)

@app.post("/bookshelves/{bookshelf_id}/books/{book_id}")
@limiter.limit("30/minute")
def add_book_to_bookshelf(
    request: Request,
    bookshelf_id: int,
    book_id: int,
    current_user: schemas.UserSchema = Depends(get_current_user),
    db = Depends(get_db)
):
    # Verify bookshelf belongs to user
    bookshelves = BookshelfService(db).get_user_bookshelves(current_user.id)
    if not any(bs.id == bookshelf_id for bs in bookshelves):
        raise HTTPException(status_code=404, detail="Bookshelf not found")
    
    # Verify book exists
    book = BookService(db).get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return BookshelfService(db).add_book_to_bookshelf(bookshelf_id, book_id)

# Data loading endpoint
@app.post("/load-kaggle-data")
@limiter.limit("5/minute")
def load_kaggle_data_endpoint(
    request: Request,
    db = Depends(get_db)
):
    try:
        # This would load data from Kaggle
        # For now, we'll create some sample data
        sample_books = [
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "genre": "Classic", "rating": 4.5, "price": 12.99},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee", "genre": "Classic", "rating": 4.8, "price": 14.99},
            {"title": "1984", "author": "George Orwell", "genre": "Dystopian", "rating": 4.6, "price": 11.99},
        ]
        
        for book_data in sample_books:
            book = schemas.BookCreate(**book_data)
            BookService(db).create_book(book)
        
        return {"message": "Sample data loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
@limiter.limit("100/minute")
def health_check(request: Request):
    return {"status": "healthy", "message": "Bkmrk'd API is running"}

@app.on_event("startup")
async def startup_event():
    logging.info("Starting Bkmrk'd API server...")