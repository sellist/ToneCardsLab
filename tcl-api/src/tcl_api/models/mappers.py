"""Mappers to convert database entities to DTOs."""

from typing import List, Optional

from tcl_api.models.db.entities import User, Deck, Card, UploadedFile, DeckInvitation
from tcl_api.models.dto import (
    UserRead,
    DeckRead,
    DeckSummary,
    CardRead,
)
from tcl_api.models.file import FileRead
from tcl_api.models.enum import RendererType


def user_to_read(
    user: User,
    owned_decks_count: int = 0,
    shared_decks_count: int = 0
) -> UserRead:
    """Convert User entity to UserRead DTO."""
    return UserRead(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        owned_decks_count=owned_decks_count,
        shared_decks_count=shared_decks_count,
    )


def card_to_read(card: Card) -> CardRead:
    """Convert Card entity to CardRead DTO."""
    return CardRead(
        card_id=card.card_id,
        front_content=card.front_content,
        back_content=card.back_content,
        front_renderer=card.front_renderer if isinstance(card.front_renderer, RendererType) else RendererType(card.front_renderer),
        back_renderer=card.back_renderer if isinstance(card.back_renderer, RendererType) else RendererType(card.back_renderer),
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


def deck_to_read(
    deck: Deck,
    cards: Optional[List[Card]] = None,
    viewer_ids: Optional[List[str]] = None
) -> DeckRead:
    """Convert Deck entity to DeckRead DTO."""
    card_list = cards or []
    viewer_list = viewer_ids or []

    return DeckRead(
        deck_id=deck.deck_id,
        owner_id=deck.owner_id,
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        cards=[card_to_read(card) for card in card_list],
        shared_with=viewer_list,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


def deck_to_summary(
    deck: Deck,
    card_count: int = 0,
    shared_with_count: int = 0
) -> DeckSummary:
    """Convert Deck entity to DeckSummary DTO."""
    return DeckSummary(
        deck_id=deck.deck_id,
        owner_id=deck.owner_id,
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        card_count=card_count,
        shared_with_count=shared_with_count,
        created_at=deck.created_at,
        updated_at=deck.updated_at,
    )


def file_to_read(file: UploadedFile) -> FileRead:
    """Convert UploadedFile entity to FileRead DTO."""
    return FileRead(
        file_id=file.file_id,
        file_url=file.file_url,
        file_name=file.file_name,
        file_size=file.file_size,
        mime_type=file.mime_type,
        uploaded_at=file.uploaded_at,
        deck_id=file.deck_id,
    )


def invitation_to_dict(invitation: DeckInvitation) -> dict:
    """Convert DeckInvitation entity to dict for API response."""
    return {
        "invitation_id": str(invitation.invitation_id),
        "deck_id": str(invitation.deck_id),
        "sender_id": str(invitation.sender_id),
        "recipient_email": invitation.recipient_email,
        "message": invitation.message,
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
        "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
        "accepted_at": invitation.accepted_at.isoformat() if invitation.accepted_at else None,
    }

