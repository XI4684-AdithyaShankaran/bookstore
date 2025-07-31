from sqlalchemy import Column, Integer, String, Sequence, DateTime
from datetime import datetime
from .book import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, Sequence("user_id_seq"), primary_key=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow) 