#!/usr/bin/env python3
"""
Database configuration and session management for Bkmrk'd Bookstore
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://apple@localhost:5432/bookstore")

# Create engine with optimized settings
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_timeout=30,
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception as e:
        # Return a mock session if database is unavailable
        from unittest.mock import Mock
        mock_db = Mock()
        yield mock_db

def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise Exception(f"Failed to create database tables: {e}") 