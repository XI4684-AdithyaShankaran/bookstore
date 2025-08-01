#!/usr/bin/env python3
"""
Cart schemas for Bkmrk'd Bookstore
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class CartItemCreate(BaseModel):
    book_id: int = Field(..., gt=0, description="Book ID")
    quantity: int = Field(..., gt=0, le=100, description="Quantity")

class CartItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0, le=100, description="New quantity")

class CartItemResponse(BaseModel):
    id: int
    book_id: int
    quantity: int
    price: float
    book: dict

class CartResponse(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponse]
    total_items: int
    total_amount: float
    created_at: datetime
    updated_at: datetime

class CartSummaryResponse(BaseModel):
    total_items: int
    total_amount: float
    item_count: int

class DiscountRequest(BaseModel):
    discount_code: str = Field(..., min_length=1, max_length=50)

class DiscountResponse(BaseModel):
    original_total: float
    discount_amount: float
    final_total: float
    discount_code: str 