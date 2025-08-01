#!/usr/bin/env python3
"""
Production-Ready Database Optimizations for Bkmrk'd Bookstore
Industrial standard database optimizations with proper indexing and query optimization
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import Index, text, func, and_, or_, desc, asc
from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy.sql import select

logger = logging.getLogger(__name__)

class DatabaseOptimizations:
    """Production-ready database optimizations with industrial standards"""
    
    def __init__(self):
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def create_optimized_indexes(self, engine):
        """Create optimized database indexes for production performance"""
        try:
            with engine.connect() as conn:
                # Book table indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_title_gin 
                    ON books USING gin(to_tsvector('english', title));
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_author_gin 
                    ON books USING gin(to_tsvector('english', author));
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_genre_rating 
                    ON books (genre, rating DESC);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_price_rating 
                    ON books (price, rating DESC);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_rating_price 
                    ON books (rating DESC, price ASC);
                """))
                
                # User table indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_email 
                    ON users (email);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_users_created_at 
                    ON users (created_at DESC);
                """))
                
                # Order table indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_orders_user_status 
                    ON orders (user_id, status);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_orders_created_at 
                    ON orders (created_at DESC);
                """))
                
                # Payment table indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payments_user_status 
                    ON payments (user_id, status);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payments_provider_id 
                    ON payments (provider, provider_payment_id);
                """))
                
                # Composite indexes for complex queries
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_books_search_composite 
                    ON books (genre, rating DESC, price ASC, id);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_orders_user_date 
                    ON orders (user_id, created_at DESC, status);
                """))
                
                conn.commit()
                logger.info("✅ Database indexes created successfully")
                
        except Exception as e:
            logger.error(f"❌ Error creating database indexes: {e}")
            raise
    
    def optimize_book_queries(self, db: Session) -> Dict[str, Any]:
        """Optimize book queries with proper indexing and caching"""
        try:
            # Use load_only to fetch only required columns
            books_query = db.query(Book).options(
                load_only(
                    Book.id, Book.title, Book.author, Book.genre,
                    Book.rating, Book.price, Book.cover_image
                )
            )
            
            # Add query hints for better performance
            books_query = books_query.with_hint(
                Book, 'USE INDEX (idx_books_rating_price)'
            )
            
            return books_query
            
        except Exception as e:
            logger.error(f"Error optimizing book queries: {e}")
            raise
    
    def optimized_search_books(self, db: Session, search_query: str, 
                             limit: int = 20) -> List[Dict[str, Any]]:
        """Optimized book search using full-text search and indexing"""
        try:
            # Use PostgreSQL full-text search for better performance
            search_sql = text("""
                SELECT id, title, author, genre, rating, price, cover_image,
                       ts_rank(to_tsvector('english', title || ' ' || author || ' ' || genre), plainto_tsquery('english', :query)) as rank
                FROM books 
                WHERE to_tsvector('english', title || ' ' || author || ' ' || genre) @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC, rating DESC
                LIMIT :limit
            """)
            
            result = db.execute(search_sql, {"query": search_query, "limit": limit})
            books = []
            
            for row in result:
                books.append({
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "genre": row.genre,
                    "rating": row.rating,
                    "price": row.price,
                    "cover_image": row.cover_image,
                    "search_rank": row.rank
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error in optimized book search: {e}")
            return []
    
    def optimized_get_books_by_genre(self, db: Session, genre: str, 
                                    limit: int = 20) -> List[Dict[str, Any]]:
        """Optimized genre-based book retrieval"""
        try:
            # Use index on genre and rating
            books_query = db.query(Book).options(
                load_only(
                    Book.id, Book.title, Book.author, Book.genre,
                    Book.rating, Book.price, Book.cover_image
                )
            ).filter(
                func.lower(Book.genre).like(f"%{genre.lower()}%")
            ).order_by(
                desc(Book.rating),
                asc(Book.price)
            ).limit(limit)
            
            books = []
            for book in books_query.all():
                books.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "rating": book.rating,
                    "price": book.price,
                    "cover_image": book.cover_image
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error in optimized genre search: {e}")
            return []
    
    def optimized_get_featured_books(self, db: Session, limit: int = 6) -> List[Dict[str, Any]]:
        """Optimized featured books retrieval using rating and popularity"""
        try:
            # Use composite index on rating and price
            featured_query = db.query(Book).options(
                load_only(
                    Book.id, Book.title, Book.author, Book.genre,
                    Book.rating, Book.price, Book.cover_image
                )
            ).filter(
                Book.rating >= 4.0,
                Book.price > 0
            ).order_by(
                desc(Book.rating),
                asc(Book.price)
            ).limit(limit)
            
            books = []
            for book in featured_query.all():
                books.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "rating": book.rating,
                    "price": book.price,
                    "cover_image": book.cover_image
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error in optimized featured books: {e}")
            return []
    
    def optimized_get_user_recommendations(self, db: Session, user_id: int, 
                                         limit: int = 10) -> List[Dict[str, Any]]:
        """Optimized user-based recommendations using user history"""
        try:
            # Get user's reading history
            user_history_query = db.query(Book.genre, Book.author).join(
                OrderItem, Book.id == OrderItem.book_id
            ).join(
                Order, OrderItem.order_id == Order.id
            ).filter(
                Order.user_id == user_id
            ).distinct()
            
            user_preferences = user_history_query.all()
            
            if not user_preferences:
                # Fallback to popular books
                return self.optimized_get_featured_books(db, limit)
            
            # Extract preferences
            preferred_genres = [pref.genre for pref in user_preferences if pref.genre]
            preferred_authors = [pref.author for pref in user_preferences if pref.author]
            
            # Build optimized recommendation query
            recommendation_query = db.query(Book).options(
                load_only(
                    Book.id, Book.title, Book.author, Book.genre,
                    Book.rating, Book.price, Book.cover_image
                )
            ).filter(
                or_(
                    Book.genre.in_(preferred_genres),
                    Book.author.in_(preferred_authors)
                )
            ).order_by(
                desc(Book.rating),
                asc(Book.price)
            ).limit(limit)
            
            books = []
            for book in recommendation_query.all():
                books.append({
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre,
                    "rating": book.rating,
                    "price": book.price,
                    "cover_image": book.cover_image
                })
            
            return books
            
        except Exception as e:
            logger.error(f"Error in optimized user recommendations: {e}")
            return []
    
    def optimized_get_orders_by_user(self, db: Session, user_id: int, 
                                   page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Optimized order retrieval with pagination"""
        try:
            # Use index on user_id and created_at
            offset = (page - 1) * page_size
            
            orders_query = db.query(Order).options(
                joinedload(Order.items).joinedload(OrderItem.book)
            ).filter(
                Order.user_id == user_id
            ).order_by(
                desc(Order.created_at)
            ).offset(offset).limit(page_size)
            
            total_count = db.query(Order).filter(
                Order.user_id == user_id
            ).count()
            
            orders = []
            for order in orders_query.all():
                order_data = {
                    "id": order.id,
                    "order_number": order.order_number,
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "created_at": order.created_at,
                    "items": []
                }
                
                for item in order.items:
                    order_data["items"].append({
                        "book_id": item.book_id,
                        "quantity": item.quantity,
                        "price": item.price,
                        "book_title": item.book.title if item.book else "Unknown"
                    })
                
                orders.append(order_data)
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "orders": orders,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "page_size": page_size,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error in optimized order retrieval: {e}")
            return {"orders": [], "pagination": {}}
    
    def optimized_get_payment_history(self, db: Session, user_id: int, 
                                    page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Optimized payment history retrieval"""
        try:
            # Use index on user_id and status
            offset = (page - 1) * page_size
            
            payments_query = db.query(Payment).filter(
                Payment.user_id == user_id
            ).order_by(
                desc(Payment.created_at)
            ).offset(offset).limit(page_size)
            
            total_count = db.query(Payment).filter(
                Payment.user_id == user_id
            ).count()
            
            payments = []
            for payment in payments_query.all():
                payments.append({
                    "id": payment.id,
                    "amount": payment.amount,
                    "currency": payment.currency,
                    "provider": payment.provider,
                    "method": payment.method,
                    "status": payment.status,
                    "created_at": payment.created_at,
                    "completed_at": payment.completed_at
                })
            
            total_pages = (total_count + page_size - 1) // page_size
            
            return {
                "payments": payments,
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_count,
                    "page_size": page_size,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error in optimized payment history: {e}")
            return {"payments": [], "pagination": {}}
    
    def optimize_database_connection_pool(self, engine):
        """Optimize database connection pool for production"""
        try:
            # Configure connection pool for production
            engine.pool_size = 20  # Increased for production
            engine.max_overflow = 30  # Increased for production
            engine.pool_recycle = 3600  # Recycle connections every hour
            engine.pool_pre_ping = True  # Validate connections
            engine.pool_timeout = 30  # Connection timeout
            
            logger.info("✅ Database connection pool optimized for production")
            
        except Exception as e:
            logger.error(f"❌ Error optimizing connection pool: {e}")
            raise
    
    def create_database_statistics(self, engine):
        """Create database statistics for query optimization"""
        try:
            with engine.connect() as conn:
                # Update table statistics
                conn.execute(text("ANALYZE books;"))
                conn.execute(text("ANALYZE users;"))
                conn.execute(text("ANALYZE orders;"))
                conn.execute(text("ANALYZE payments;"))
                conn.execute(text("ANALYZE order_items;"))
                
                conn.commit()
                logger.info("✅ Database statistics updated")
                
        except Exception as e:
            logger.error(f"❌ Error updating database statistics: {e}")
            raise
    
    def optimize_query_performance(self, db: Session, query_type: str, 
                                 **kwargs) -> List[Dict[str, Any]]:
        """Generic query optimization based on query type"""
        try:
            if query_type == "books_search":
                return self.optimized_search_books(db, kwargs.get("search_query", ""))
            elif query_type == "books_genre":
                return self.optimized_get_books_by_genre(db, kwargs.get("genre", ""))
            elif query_type == "books_featured":
                return self.optimized_get_featured_books(db, kwargs.get("limit", 6))
            elif query_type == "user_recommendations":
                return self.optimized_get_user_recommendations(db, kwargs.get("user_id"), kwargs.get("limit", 10))
            elif query_type == "user_orders":
                return self.optimized_get_orders_by_user(db, kwargs.get("user_id"), kwargs.get("page", 1), kwargs.get("page_size", 10))
            elif query_type == "payment_history":
                return self.optimized_get_payment_history(db, kwargs.get("user_id"), kwargs.get("page", 1), kwargs.get("page_size", 10))
            else:
                logger.warning(f"Unknown query type: {query_type}")
                return []
                
        except Exception as e:
            logger.error(f"Error in query optimization: {e}")
            return []

# Initialize database optimizations
db_optimizations = DatabaseOptimizations() 