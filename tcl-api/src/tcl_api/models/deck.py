"""Deck-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from .common import TimestampMixin, OwnershipMixin, IdResponse
from .card import Card


class DeckBase(BaseModel):
    """Base deck model with common fields."""
    title: str = Field(..., min_length=1, max_length=200, description="Deck title")
    description: Optional[str] = Field(None, max_length=1000, description="Deck description")


class DeckCreate(DeckBase):
    """Request to create a new deck."""
    cards: List[Card] = Field(default_factory=list, description="Initial cards for the deck")
    is_public: bool = Field(default=False, description="Whether deck is publicly accessible")


class DeckUpdate(BaseModel):
    """Request to update an existing deck."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated title")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    cards: Optional[List[Card]] = Field(None, description="Updated cards list")


class DeckSummary(DeckBase, OwnershipMixin):
    """Summary view of a deck (for list endpoints)."""
    deck_id: str = Field(..., description="UUID of the deck")
    card_count: int = Field(..., description="Number of cards in the deck")
    shared_with_count: int = Field(default=0, description="Number of users with viewer access")


class DeckSummaryResponse(DeckSummary, TimestampMixin):
    """Deck summary response with timestamps."""
    pass


class Deck(DeckBase, OwnershipMixin):
    """Full deck model including all cards."""
    deck_id: str = Field(..., description="UUID of the deck")
    cards: List[Card] = Field(default_factory=list, description="All cards in the deck")
    shared_with: List[str] = Field(
        default_factory=list,
        description="List of user IDs with viewer access"
    )


class DeckResponse(Deck, TimestampMixin):
    """Full deck response with timestamps and metadata."""
    pass


class DeckListResponse(BaseModel):
    """Response for deck list endpoints with categorization."""
    owned_decks: List[DeckSummaryResponse] = Field(
        default_factory=list,
        description="Decks owned by the user"
    )
    shared_decks: List[DeckSummaryResponse] = Field(
        default_factory=list,
        description="Decks shared with the user (viewer access)"
    )


class DeckStatistics(BaseModel):
    """Deck statistics response."""
    deck_id: str = Field(..., description="UUID of the deck")
    card_count: int = Field(..., description="Number of cards in the deck")
    last_modified: str = Field(..., description="ISO 8601 timestamp of last modification")
    view_count: Optional[int] = Field(None, description="Number of times deck has been viewed")
    usage_stats: Optional[dict] = Field(None, description="Additional usage statistics")


class DeckExportFormat(str, Enum):
    """Available export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class DeckExportRequest(BaseModel):
    """Request to export a deck."""
    format: DeckExportFormat = Field(..., description="Export format")


class DeckImportRequest(BaseModel):
    """Request to import a deck."""
    data: str = Field(..., description="Deck data in JSON or CSV format")
    format: DeckExportFormat = Field(..., description="Format of the import data")


class BulkDeleteDecksRequest(BaseModel):
    """Request to delete multiple decks."""
    deck_ids: List[str] = Field(..., min_length=1, description="List of deck IDs to delete")


class TogglePublicStatusRequest(BaseModel):
    """Request to toggle deck public status."""
    is_public: bool = Field(..., description="New public status")

