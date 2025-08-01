from pydantic import BaseModel
from typing import List
from .book import BookSchema

class SearchResponse(BaseModel):
    books: List[BookSchema]
    total: int
    page: int
    limit: int
    hasMore: bool 