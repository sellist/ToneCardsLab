"""Deck-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from .base import ExportableModel
from .common import OwnershipMixin
from .card import Card


class DeckBase(ExportableModel):
    title: str = Field(..., min_length=1, max_length=200, description="Deck title")
    description: Optional[str] = Field(None, max_length=1000, description="Deck description")


class DeckCreate(DeckBase):
    cards: List[Card] = Field(default_factory=list, description="Initial cards for the deck")
    is_public: bool = Field(default=False, description="Whether deck is publicly accessible")


class DeckUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated title")
    description: Optional[str] = Field(None, max_length=1000, description="Updated description")
    cards: Optional[List[Card]] = Field(None, description="Updated cards list")


class DeckSummary(DeckBase, OwnershipMixin):
    deck_id: str = Field(..., description="UUID of the deck")
    card_count: int = Field(..., description="Number of cards in the deck")
    shared_with_count: int = Field(default=0, description="Number of users with viewer access")


class Deck(DeckBase, OwnershipMixin):
    deck_id: str = Field(..., description="UUID of the deck")
    cards: List[Card] = Field(default_factory=list, description="All cards in the deck")
    shared_with: List[str] = Field(
        default_factory=list,
        description="List of user IDs with viewer access"
    )


class DeckExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"


class DeckExportRequest(BaseModel):
    format: DeckExportFormat = Field(..., description="Export format")


class DeckImportRequest(BaseModel):
    data: str = Field(..., description="Deck data in JSON or CSV format")
    format: DeckExportFormat = Field(..., description="Format of the import data")


class BulkDeleteDecksRequest(BaseModel):
    deck_ids: List[str] = Field(..., min_length=1, description="List of deck IDs to delete")


class TogglePublicStatusRequest(BaseModel):
    is_public: bool = Field(..., description="New public status")

