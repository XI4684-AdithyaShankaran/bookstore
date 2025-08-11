#!/usr/bin/env python3
"""
Database configuration and session management for Bkmrk'd Bookstore
"""

import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bookstore_user:bookstore_pass@localhost:5432/bookstore_db")

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
    """Get database session with proper error handling"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise Exception(f"Failed to create database tables: {e}") 