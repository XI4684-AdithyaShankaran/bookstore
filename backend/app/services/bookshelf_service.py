from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.bookshelf import Bookshelf, BookshelfBook

class BookshelfService:
    def __init__(self, db: Session):
        self.db = db

    def create_bookshelf(self, user_id: int, name: str, description: Optional[str] = None, is_public: bool = False) -> Bookshelf:
        db_bookshelf = Bookshelf(
            user_id=user_id,
            name=name,
            description=description,
            is_public=1 if is_public else 0
        )
        self.db.add(db_bookshelf)
        self.db.commit()
        self.db.refresh(db_bookshelf)
        return db_bookshelf

    def get_user_bookshelves(self, user_id: int) -> List[Bookshelf]:
        return self.db.query(Bookshelf).filter(Bookshelf.user_id == user_id).all()

    def add_book_to_bookshelf(self, bookshelf_id: int, book_id: int) -> BookshelfBook:
        db_bookshelf_book = BookshelfBook(
            bookshelf_id=bookshelf_id,
            book_id=book_id
        )
        self.db.add(db_bookshelf_book)
        self.db.commit()
        self.db.refresh(db_bookshelf_book)
        return db_bookshelf_book 