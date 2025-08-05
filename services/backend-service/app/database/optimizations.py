#!/usr/bin/env python3
"""
Database optimizations and performance enhancements for Bkmrk'd Bookstore
Industrial standard optimizations with competitive programming algorithms
"""

import logging
import time
import threading
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, text, Index, func, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session, joinedload, load_only
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import psutil
import gc
import os

logger = logging.getLogger(__name__)

class DatabaseOptimizations:
    """Industrial standard database optimizations"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        self._connection_pool = {}
        self._pool_lock = threading.RLock()
        self._last_optimization = time.time()
        self.OPTIMIZATION_INTERVAL = 3600  # 1 hour
        
    def initialize_engine(self):
        """Initialize optimized database engine"""
        try:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=20,
                max_overflow=30,
                pool_recycle=3600,
                pool_timeout=30,
                pool_pre_ping=True,
                echo=False,
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "bookstore_backend"
                }
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("✅ Database engine initialized with optimizations")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database engine: {e}")
            raise
    
    def create_performance_indexes(self, session: Session):
        """Create performance indexes for optimal query speed"""
        try:
            # Book table indexes
            indexes = [
                # Title search index
                Index('idx_books_title_lower', text('LOWER(title)')),
                
                # Author search index
                Index('idx_books_author_lower', text('LOWER(author)')),
                
                # Rating and popularity index
                Index('idx_books_rating_popularity', 'rating', 'ratings_count'),
                
                # Genre index
                Index('idx_books_genre', 'genre'),
                
                # Price range index
                Index('idx_books_price', 'price'),
                
                # Publication year index
                Index('idx_books_year', 'year'),
                
                # ISBN indexes
                Index('idx_books_isbn', 'isbn'),
                Index('idx_books_isbn13', 'isbn13'),
                
                # Language index
                Index('idx_books_language', 'language'),
                
                # Composite indexes for common queries
                Index('idx_books_genre_rating', 'genre', 'rating'),
                Index('idx_books_year_rating', 'year', 'rating'),
                Index('idx_books_price_rating', 'price', 'rating'),
                
                # User table indexes
                Index('idx_users_email', 'email'),
                Index('idx_users_active', 'is_active'),
                
                # Order table indexes
                Index('idx_orders_user_id', 'user_id'),
                Index('idx_orders_status', 'status'),
                Index('idx_orders_created_at', 'created_at'),
                
                # Cart table indexes
                Index('idx_cart_user_id', 'user_id'),
                Index('idx_cart_book_id', 'book_id'),
                
                # Bookshelf indexes
                Index('idx_bookshelves_user_id', 'user_id'),
                Index('idx_bookshelves_name', 'name'),
                
                # Wishlist indexes
                Index('idx_wishlist_user_book', 'user_id', 'book_id'),
            ]
            
            for index in indexes:
                try:
                    session.execute(text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table.name} ({', '.join(index.expressions)})"))
                except Exception as e:
                    logger.warning(f"Index {index.name} creation failed: {e}")
            
            session.commit()
            logger.info("✅ Performance indexes created successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to create performance indexes: {e}")
            raise
    
    def optimize_table_statistics(self, session: Session):
        """Update table statistics for query optimization"""
        try:
            tables = ['books', 'users', 'orders', 'cart', 'bookshelves', 'wishlist_items']
            
            for table in tables:
                session.execute(text(f"ANALYZE {table}"))
            
            session.commit()
            logger.info("✅ Table statistics updated for query optimization")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to update table statistics: {e}")
            raise
    
    def vacuum_database(self, session: Session):
        """Vacuum database to reclaim storage and update statistics"""
        try:
            session.execute(text("VACUUM ANALYZE"))
            session.commit()
            logger.info("✅ Database vacuum completed")
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Failed to vacuum database: {e}")
            raise
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status and metrics"""
        try:
            if not self.engine:
                return {"error": "Engine not initialized"}
            
            pool = self.engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
                "total_connections": pool.size() + pool.overflow()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get pool status: {e}")
            return {"error": str(e)}
    
    def optimize_memory_usage(self):
        """Optimize memory usage for database operations"""
        try:
            # Force garbage collection
            gc.collect()
            
            # Get memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            logger.info(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
            
            # If memory usage is high, force more aggressive cleanup
            if memory_info.rss > 500 * 1024 * 1024:  # 500MB
                gc.collect()
                logger.info("Forced memory cleanup due to high usage")
            
        except Exception as e:
            logger.error(f"❌ Failed to optimize memory: {e}")
    
    def run_periodic_optimizations(self, session: Session):
        """Run periodic database optimizations"""
        current_time = time.time()
        
        if current_time - self._last_optimization > self.OPTIMIZATION_INTERVAL:
            try:
                logger.info("🔄 Running periodic database optimizations...")
                
                # Update statistics
                self.optimize_table_statistics(session)
                
                # Vacuum database
                self.vacuum_database(session)
                
                # Optimize memory
                self.optimize_memory_usage()
                
                self._last_optimization = current_time
                logger.info("✅ Periodic optimizations completed")
                
            except Exception as e:
                logger.error(f"❌ Periodic optimizations failed: {e}")
    
    def get_query_performance_metrics(self, session: Session) -> Dict[str, Any]:
        """Get query performance metrics"""
        try:
            # Get slow query statistics
            slow_queries = session.execute(text("""
                SELECT query, calls, total_time, mean_time
                FROM pg_stat_statements
                WHERE mean_time > 100
                ORDER BY mean_time DESC
                LIMIT 10
            """)).fetchall()
            
            # Get table statistics
            table_stats = session.execute(text("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
            """)).fetchall()
            
            return {
                "slow_queries": [dict(row._mapping) for row in slow_queries],
                "table_stats": [dict(row._mapping) for row in table_stats],
                "pool_status": self.get_connection_pool_status()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance metrics: {e}")
            return {"error": str(e)}

# Global database optimizations instance
db_optimizations = DatabaseOptimizations(os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/bookstore")) 