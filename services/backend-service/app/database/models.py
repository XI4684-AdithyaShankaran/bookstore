from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between users and books (wishlist)
wishlist = Table(
    'wishlist',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True)
)

# Association table for many-to-many relationship between bookshelves and books
bookshelf_books = Table(
    'bookshelf_books',
    Base.metadata,
    Column('bookshelf_id', Integer, ForeignKey('bookshelves.id'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ratings = relationship("Rating", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    bookshelves = relationship("Bookshelf", back_populates="user")
    wishlist_books = relationship("Book", secondary=wishlist, back_populates="wishlisted_by")

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    description = Column(Text)
    genre = Column(String, index=True)
    price = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    image_url = Column(String)
    isbn = Column(String, unique=True, index=True)
    publication_date = Column(DateTime)
    page_count = Column(Integer)
    language = Column(String, default="English")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ratings = relationship("Rating", back_populates="book")
    cart_items = relationship("CartItem", back_populates="book")
    bookshelves = relationship("Bookshelf", secondary=bookshelf_books, back_populates="books")
    wishlisted_by = relationship("User", secondary=wishlist, back_populates="wishlist_books")

class Rating(Base):
    __tablename__ = "ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    rating = Column(Float, nullable=False)
    review = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ratings")
    book = relationship("Book", back_populates="ratings")

class CartItem(Base):
    __tablename__ = "cart_items"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    book = relationship("Book", back_populates="cart_items")

class Bookshelf(Base):
    __tablename__ = "bookshelves"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="bookshelves")
    books = relationship("Book", secondary=bookshelf_books, back_populates="bookshelves") 