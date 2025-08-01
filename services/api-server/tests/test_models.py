import pytest
from sqlalchemy.orm import Session
from datetime import datetime
from main import Book, User, Bookshelf, BookshelfBook

class TestBookModel:
    """Test Book model functionality"""
    
    def test_create_book(self, db_session: Session, sample_book_data):
        """Test creating a book"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        assert book.id is not None
        assert book.title == sample_book_data["title"]
        assert book.author == sample_book_data["author"]
        assert book.created_at is not None
        assert book.updated_at is not None
    
    def test_book_string_representation(self, db_session: Session, sample_book_data):
        """Test book string representation"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        assert str(book) == f"<Book {book.id}: {sample_book_data['title']}>"
    
    def test_book_update(self, db_session: Session, sample_book_data):
        """Test updating a book"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        original_updated_at = book.updated_at
        book.title = "Updated Title"
        db_session.commit()
        
        assert book.title == "Updated Title"
        assert book.updated_at > original_updated_at

class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user(self, db_session: Session, sample_user_data):
        """Test creating a user"""
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == sample_user_data["email"]
        assert user.username == sample_user_data["username"]
        assert user.is_active == 1
        assert user.created_at is not None
    
    def test_user_string_representation(self, db_session: Session, sample_user_data):
        """Test user string representation"""
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        assert str(user) == f"<User {user.id}: {sample_user_data['username']}>"

class TestBookshelfModel:
    """Test Bookshelf model functionality"""
    
    def test_create_bookshelf(self, db_session: Session, sample_user_data):
        """Test creating a bookshelf"""
        # Create user first
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        bookshelf = Bookshelf(
            user_id=user.id,
            name="My Bookshelf",
            description="A test bookshelf",
            is_public=0
        )
        db_session.add(bookshelf)
        db_session.commit()
        
        assert bookshelf.id is not None
        assert bookshelf.user_id == user.id
        assert bookshelf.name == "My Bookshelf"
        assert bookshelf.is_public == 0
        assert bookshelf.created_at is not None

class TestBookshelfBookModel:
    """Test BookshelfBook model functionality"""
    
    def test_add_book_to_bookshelf(self, db_session: Session, sample_book_data, sample_user_data):
        """Test adding a book to a bookshelf"""
        # Create user
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        # Create bookshelf
        bookshelf = Bookshelf(
            user_id=user.id,
            name="My Bookshelf",
            description="A test bookshelf"
        )
        db_session.add(bookshelf)
        db_session.commit()
        
        # Add book to bookshelf
        bookshelf_book = BookshelfBook(
            bookshelf_id=bookshelf.id,
            book_id=book.id
        )
        db_session.add(bookshelf_book)
        db_session.commit()
        
        assert bookshelf_book.id is not None
        assert bookshelf_book.bookshelf_id == bookshelf.id
        assert bookshelf_book.book_id == book.id
        assert bookshelf_book.added_at is not None

class TestModelRelationships:
    """Test model relationships"""
    
    def test_user_bookshelves_relationship(self, db_session: Session, sample_user_data):
        """Test user-bookshelf relationship"""
        # Create user
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password="hashed_password_123"
        )
        db_session.add(user)
        db_session.commit()
        
        # Create multiple bookshelves for user
        bookshelf1 = Bookshelf(user_id=user.id, name="Bookshelf 1")
        bookshelf2 = Bookshelf(user_id=user.id, name="Bookshelf 2")
        db_session.add_all([bookshelf1, bookshelf2])
        db_session.commit()
        
        # Query bookshelves for user
        user_bookshelves = db_session.query(Bookshelf).filter(Bookshelf.user_id == user.id).all()
        assert len(user_bookshelves) == 2
        assert bookshelf1 in user_bookshelves
        assert bookshelf2 in user_bookshelves 