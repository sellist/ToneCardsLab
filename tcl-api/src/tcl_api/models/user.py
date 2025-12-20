from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from .common import TimestampMixin


class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    preferences: Optional[dict] = None


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    preferences: Optional[dict] = None


class UserDeleteConfirm(BaseModel):
    confirmation: str


class User(TimestampMixin):
    user_id: str
    email: str
    name: Optional[str] = None
    preferences: dict = Field(default_factory=dict)
    owned_decks_count: int = 0
    shared_decks_count: int = 0

