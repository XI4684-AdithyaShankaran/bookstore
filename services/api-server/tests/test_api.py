import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import Book, User, get_password_hash

class TestBooksAPI:
    """Test book-related API endpoints"""
    
    def test_get_books_empty(self, client: TestClient):
        """Test getting books when database is empty"""
        response = client.get("/books")
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_books_with_data(self, client: TestClient, db_session: Session, sample_book_data):
        """Test getting books with data in database"""
        # Create a book in the database
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get("/books")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == sample_book_data["title"]
    
    def test_get_books_with_search(self, client: TestClient, db_session: Session, sample_book_data):
        """Test searching books"""
        # Create a book in the database
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get("/books?search=Test")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == sample_book_data["title"]
    
    def test_get_books_with_genre_filter(self, client: TestClient, db_session: Session, sample_book_data):
        """Test filtering books by genre"""
        # Create a book in the database
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get("/books?genre=Fiction")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 1
        assert books[0]["genre"] == "Fiction"
    
    def test_get_book_by_id(self, client: TestClient, db_session: Session, sample_book_data):
        """Test getting a specific book by ID"""
        # Create a book in the database
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get(f"/books/{book.id}")
        assert response.status_code == 200
        book_data = response.json()
        assert book_data["title"] == sample_book_data["title"]
    
    def test_get_book_by_id_not_found(self, client: TestClient):
        """Test getting a book that doesn't exist"""
        response = client.get("/books/999")
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

class TestUsersAPI:
    """Test user-related API endpoints"""
    
    def test_register_user(self, client: TestClient, sample_user_data):
        """Test user registration"""
        response = client.post("/register", json=sample_user_data)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == sample_user_data["email"]
        assert user_data["username"] == sample_user_data["username"]
        assert "password" not in user_data  # Password should not be returned
    
    def test_register_user_duplicate_email(self, client: TestClient, db_session: Session, sample_user_data):
        """Test registering a user with duplicate email"""
        # Create first user
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Try to register with same email
        response = client.post("/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_login_user(self, client: TestClient, db_session: Session, sample_user_data):
        """Test user login"""
        # Create user first
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Login
        response = client.post("/token", data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"

class TestBookshelvesAPI:
    """Test bookshelf-related API endpoints"""
    
    def test_create_bookshelf(self, client: TestClient, db_session: Session, sample_user_data):
        """Test creating a bookshelf"""
        # Create user first
        user = User(
            email=sample_user_data["email"],
            username=sample_user_data["username"],
            hashed_password=get_password_hash(sample_user_data["password"])
        )
        db_session.add(user)
        db_session.commit()
        
        # Login to get token
        login_response = client.post("/token", data={
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        token = login_response.json()["access_token"]
        
        # Create bookshelf
        bookshelf_data = {
            "name": "My Test Bookshelf",
            "description": "A test bookshelf",
            "is_public": False
        }
        
        response = client.post("/bookshelves", 
                             json=bookshelf_data,
                             headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        bookshelf = response.json()
        assert bookshelf["name"] == bookshelf_data["name"]

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client: TestClient):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"} 