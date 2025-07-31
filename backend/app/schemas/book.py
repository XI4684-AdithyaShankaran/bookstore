from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author: str
    year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    rating: Optional[float] = None
    pages: Optional[int] = None
    language: Optional[str] = None
    publisher: Optional[str] = None
    cover_image: Optional[str] = None
    price: Optional[float] = None

class BookCreate(BookBase):
    pass

class BookSchema(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 