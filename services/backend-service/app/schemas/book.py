from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BookBase(BaseModel):
    title: str
    author: str
    genre: str
    description: Optional[str] = None
    price: float
    rating: Optional[float] = 0.0
    image_url: Optional[str] = None
    isbn: Optional[str] = None
    publication_date: Optional[datetime] = None
    page_count: Optional[int] = None
    language: Optional[str] = None

class BookCreate(BookBase):
    pass

class BookSchema(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookResponse(BookSchema):
    pass 