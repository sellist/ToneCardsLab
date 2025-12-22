from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .common import TimestampMixin


class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


class UserDeleteConfirm(BaseModel):
    confirmation: str


class User(TimestampMixin):
    user_id: str
    email: str
    name: Optional[str] = None
    owned_decks_count: int = 0
    shared_decks_count: int = 0

