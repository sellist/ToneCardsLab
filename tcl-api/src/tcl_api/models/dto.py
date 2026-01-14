"""Data Transfer Objects (DTOs) for API requests and responses."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import EmailStr, Field
from sqlmodel import SQLModel

from tcl_api.models.enum import RendererType, DeckExportFormat


class UserCreate(SQLModel):
    email: EmailStr = Field(description="User's email address")
    name: Optional[str] = Field(default=None, max_length=100, description="User's display name")


class UserUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=100, description="Updated display name")


class UserRead(SQLModel):
    user_id: UUID
    email: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    owned_decks_count: int = 0
    shared_decks_count: int = 0


class UserDeleteConfirm(SQLModel):
    confirmation: str = Field(description="Type 'DELETE' to confirm")

class CardCreate(SQLModel):
    deck_id: UUID = Field(description="UUID of the parent deck (required)")
    front_content: str = Field(description="Content for front of card")
    back_content: str = Field(description="Content for back of card")
    front_renderer: RendererType = Field(default=RendererType.STRING)
    back_renderer: RendererType = Field(default=RendererType.STRING)


class CardUpdate(SQLModel):
    front_content: Optional[str] = Field(default=None)
    back_content: Optional[str] = Field(default=None)
    front_renderer: Optional[RendererType] = Field(default=None)
    back_renderer: Optional[RendererType] = Field(default=None)


class CardRead(SQLModel):
    card_id: UUID
    front_content: str
    back_content: str
    front_renderer: RendererType
    back_renderer: RendererType
    created_at: datetime
    updated_at: datetime


class ReorderCardsRequest(SQLModel):
    card_order: List[str] = Field(
        min_length=1,
        description="Ordered list of card IDs"
    )


class DeckCreate(SQLModel):
    title: str = Field(min_length=1, max_length=200, description="Deck title")
    description: Optional[str] = Field(default=None, max_length=1000)
    cards: List[CardCreate] = Field(default_factory=list, description="Optional list of cards to add (can be empty)")
    is_public: bool = Field(default=False)


class DeckUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    cards: Optional[List[CardCreate]] = Field(default=None)


class DeckSummary(SQLModel):
    deck_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str] = None
    is_public: bool = False
    card_count: int = 0
    shared_with_count: int = 0
    created_at: datetime
    updated_at: datetime


class DeckRead(SQLModel):
    deck_id: UUID
    owner_id: UUID
    title: str
    description: Optional[str] = None
    is_public: bool = False
    cards: List[CardRead] = Field(default_factory=list)
    shared_with: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DeckExportRequest(SQLModel):
    format: DeckExportFormat = Field(description="Export format")


class DeckImportRequest(SQLModel):
    data: str = Field(description="Deck data in JSON or CSV format")
    format: DeckExportFormat = Field(description="Format of the import data")


class BulkDeleteDecksRequest(SQLModel):
    deck_ids: List[UUID] = Field(min_length=1, description="List of deck IDs to delete")


class TogglePublicStatusRequest(SQLModel):
    is_public: bool = Field(description="New public status")


class ViewersResponse(SQLModel):
    deck_id: UUID
    viewer_ids: List[UUID] = Field(default_factory=list)


class EditViewersRequest(SQLModel):
    add_viewer_ids: List[UUID] = Field(default_factory=list)
    remove_viewer_ids: List[UUID] = Field(default_factory=list)


class ShareByEmailRequest(SQLModel):
    recipient_email: EmailStr
    message: Optional[str] = Field(default=None, max_length=500)


class ShareByEmailResponse(SQLModel):
    invitation_id: UUID
    status: str = "sent"
    expires_at: Optional[datetime] = None


class ReportRequest(SQLModel):
    reason: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
