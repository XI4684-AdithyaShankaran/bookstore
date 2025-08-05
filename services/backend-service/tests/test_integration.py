import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import Book, User, get_password_hash

class TestBookstoreIntegration:
    """Integration tests for the bookstore application"""
    
    def test_complete_user_journey(self, client: TestClient, db_session: Session):
        """Test complete user journey: register, login, create bookshelf, add book"""
        # 1. Register user
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
        
        register_response = client.post("/register", json=user_data)
        assert register_response.status_code == 200
        user = register_response.json()
        
        # 2. Login user
        login_response = client.post("/token", data={
            "username": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]
        
        # 3. Create a book
        book_data = {
            "title": "Integration Test Book",
            "author": "Integration Test Author",
            "year": 2023,
            "genre": "Fiction",
            "description": "A book for integration testing",
            "isbn": "1234567890123",
            "rating": 4.5,
            "pages": 300,
            "language": "English",
            "publisher": "Test Publisher",
            "cover_image": "https://example.com/cover.jpg",
            "price": 19.99
        }
        
        # Add book to database
        book = Book(**book_data)
        db_session.add(book)
        db_session.commit()
        
        # 4. Search for the book
        search_response = client.get("/books?search=Integration")
        assert search_response.status_code == 200
        books = search_response.json()
        assert len(books) == 1
        assert books[0]["title"] == book_data["title"]
        
        # 5. Create bookshelf
        bookshelf_data = {
            "name": "My Integration Bookshelf",
            "description": "A bookshelf created during integration testing",
            "is_public": False
        }
        
        bookshelf_response = client.post("/bookshelves", 
                                       json=bookshelf_data,
                                       headers={"Authorization": f"Bearer {token}"})
        assert bookshelf_response.status_code == 200
        bookshelf = bookshelf_response.json()
        
        # 6. Add book to bookshelf
        add_book_response = client.post(f"/bookshelves/{bookshelf['id']}/books/{book.id}",
                                       headers={"Authorization": f"Bearer {token}"})
        assert add_book_response.status_code == 200
    
    def test_search_and_filter_integration(self, client: TestClient, db_session: Session):
        """Test search and filter functionality together"""
        # Create multiple books
        books_data = [
            {
                "title": "Fiction Book 1",
                "author": "Author A",
                "genre": "Fiction",
                "year": 2023,
                "description": "A fiction book",
                "isbn": "1234567890123",
                "rating": 4.5,
                "pages": 300,
                "language": "English",
                "publisher": "Publisher A",
                "cover_image": "https://example.com/cover1.jpg",
                "price": 19.99
            },
            {
                "title": "Non-Fiction Book 1",
                "author": "Author B",
                "genre": "Non-Fiction",
                "year": 2023,
                "description": "A non-fiction book",
                "isbn": "1234567890124",
                "rating": 4.0,
                "pages": 250,
                "language": "English",
                "publisher": "Publisher B",
                "cover_image": "https://example.com/cover2.jpg",
                "price": 24.99
            },
            {
                "title": "Fiction Book 2",
                "author": "Author C",
                "genre": "Fiction",
                "year": 2022,
                "description": "Another fiction book",
                "isbn": "1234567890125",
                "rating": 4.8,
                "pages": 350,
                "language": "English",
                "publisher": "Publisher C",
                "cover_image": "https://example.com/cover3.jpg",
                "price": 21.99
            }
        ]
        
        # Add books to database
        for book_data in books_data:
            book = Book(**book_data)
            db_session.add(book)
        db_session.commit()
        
        # Test search functionality
        search_response = client.get("/books?search=Fiction")
        assert search_response.status_code == 200
        fiction_books = search_response.json()
        assert len(fiction_books) == 2
        
        # Test genre filter
        genre_response = client.get("/books?genre=Fiction")
        assert genre_response.status_code == 200
        fiction_books_by_genre = genre_response.json()
        assert len(fiction_books_by_genre) == 2
        
        # Test combined search and filter
        combined_response = client.get("/books?search=Book&genre=Fiction")
        assert combined_response.status_code == 200
        combined_results = combined_response.json()
        assert len(combined_results) == 2
    
    def test_recommendation_integration(self, client: TestClient, db_session: Session):
        """Test recommendation system integration"""
        # Create books for recommendations
        books_data = [
            {
                "title": "Book A",
                "author": "Author A",
                "genre": "Fiction",
                "year": 2023,
                "description": "A fiction book about adventure",
                "isbn": "1234567890123",
                "rating": 4.5,
                "pages": 300,
                "language": "English",
                "publisher": "Publisher A",
                "cover_image": "https://example.com/cover1.jpg",
                "price": 19.99
            },
            {
                "title": "Book B",
                "author": "Author B",
                "genre": "Fiction",
                "year": 2023,
                "description": "Another fiction book about adventure",
                "isbn": "1234567890124",
                "rating": 4.0,
                "pages": 250,
                "language": "English",
                "publisher": "Publisher B",
                "cover_image": "https://example.com/cover2.jpg",
                "price": 24.99
            }
        ]
        
        # Add books to database
        for book_data in books_data:
            book = Book(**book_data)
            db_session.add(book)
        db_session.commit()
        
        # Get the first book for recommendations
        first_book = db_session.query(Book).first()
        
        # Test book recommendations
        recommendations_response = client.get(f"/books/{first_book.id}/recommendations")
        assert recommendations_response.status_code == 200
        recommendations = recommendations_response.json()
        assert "recommendations" in recommendations or isinstance(recommendations, list)
    
    def test_error_handling_integration(self, client: TestClient):
        """Test error handling across the application"""
        # Test invalid book ID
        response = client.get("/books/999999")
        assert response.status_code == 404
        
        # Test invalid user registration
        invalid_user_data = {
            "email": "invalid-email",
            "username": "",
            "password": "123"
        }
        response = client.post("/register", json=invalid_user_data)
        assert response.status_code == 422  # Validation error
        
        # Test invalid login
        response = client.post("/token", data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        
        # Test unauthorized access
        response = client.post("/bookshelves", json={
            "name": "Test Bookshelf",
            "description": "Test",
            "is_public": False
        })
        assert response.status_code == 401  # Unauthorized 