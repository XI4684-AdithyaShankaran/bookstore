from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserSchema(UserBase):
    id: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True 