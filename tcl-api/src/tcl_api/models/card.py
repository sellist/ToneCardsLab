"""Card-related Pydantic models."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RendererType(str, Enum):
    """Available content renderer types."""
    STRING = "string"
    MARKDOWN = "markdown"
    ABC_JS = "abc_js"
    IMAGE = "image"
    LATEX = "latex"
    MERMAID = "mermaid"


class CardBase(BaseModel):
    """Base card model with common fields."""
    front_content: str = Field(..., description="Content to display on front of card")
    back_content: str = Field(..., description="Content to display on back of card")
    front_renderer: RendererType = Field(
        default=RendererType.STRING,
        description="Renderer type for front content"
    )
    back_renderer: RendererType = Field(
        default=RendererType.STRING,
        description="Renderer type for back content"
    )


class CardCreate(CardBase):
    """Request to create a new card."""
    pass


class CardUpdate(BaseModel):
    """Request to update an existing card."""
    front_content: Optional[str] = Field(None, description="Updated front content")
    back_content: Optional[str] = Field(None, description="Updated back content")
    front_renderer: Optional[RendererType] = Field(None, description="Updated front renderer")
    back_renderer: Optional[RendererType] = Field(None, description="Updated back renderer")


class Card(CardBase):
    """Full card model with ID."""
    card_id: str = Field(..., description="UUID of the card")


class CardResponse(Card):
    """Card response model."""
    pass


class ReorderCardsRequest(BaseModel):
    """Request to reorder cards in a deck."""
    card_order: list[str] = Field(
        ...,
        description="Ordered list of card IDs representing new order",
        min_length=1
    )

