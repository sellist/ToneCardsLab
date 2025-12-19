"""Deck management router."""

from typing import Optional, List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.models.base import EntitySerializer
from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import DeckDAO, UserDAO, CardDAO, DeckViewerDAO
from tcl_api.models.deck import (
    DeckCreate,
    DeckUpdate,
    BulkDeleteDecksRequest,
    Deck,
    DeckSummary
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.response import ApiResponse

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("/", response_model=ApiResponse[Deck])
def create_deck(
    deck_data: DeckCreate,
    owner_id: UUID = Query(..., description="User ID of deck owner"),
    db: Session = Depends(get_db)
):
    """Create a new deck with optional initial cards."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    # Verify owner exists
    owner = user_dao.get_by_id(owner_id)
    if not owner or owner.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner user not found"
        )

    # Create deck
    deck_dict = {
        "owner_id": owner_id,
        "title": deck_data.title,
        "description": deck_data.description,
        "is_public": deck_data.is_public
    }
    deck = deck_dao.create(deck_dict)

    # Create cards if provided
    created_cards = []
    if deck_data.cards:
        for i, card_data in enumerate(deck_data.cards):
            card_dict = {
                "deck_id": deck.deck_id,
                "front_content": card_data.front_content,
                "back_content": card_data.back_content,
                "front_renderer": card_data.front_renderer,
                "back_renderer": card_data.back_renderer,
                "position": i
            }
            card = card_dao.create(card_dict)
            created_cards.append(card)

    deck_response_data = EntitySerializer.serialize_deck(deck, created_cards, [])

    return ApiResponseBuilder.created().data(deck_response_data).message("Deck created successfully").build()


@router.get("/{deck_id}", response_model=ApiResponse[Deck])
def get_deck(deck_id: UUID, db: Session = Depends(get_db)):
    """Get full deck details including all cards."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)
    viewer_dao = DeckViewerDAO(db)

    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Get cards and viewers
    cards = card_dao.get_by_deck(deck_id)
    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    deck_data = EntitySerializer.serialize_deck(deck, cards, viewer_ids)

    return ApiResponseBuilder.ok().data(deck_data).build()


@router.get("/", response_model=ApiResponse[List[DeckSummary]])
def list_decks(
    owner_id: Optional[UUID] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)
    viewer_dao = DeckViewerDAO(db)

    if search:
        decks = deck_dao.search_decks(
            query=search,
            owner_id=owner_id,
            is_public=is_public,
            skip=skip,
            limit=limit
        )
    elif owner_id:
        decks = deck_dao.get_by_owner(owner_id, skip=skip, limit=limit)
    elif is_public:
        decks = deck_dao.get_public_decks(skip=skip, limit=limit)
    else:
        decks = deck_dao.get_multi(skip=skip, limit=limit)

    result = []
    for deck in decks:
        if deck.deleted_at:
            continue

        card_count = card_dao.count_by_deck(deck.deck_id)
        viewer_count = len(viewer_dao.get_viewer_ids(deck.deck_id))

        result.append(EntitySerializer.serialize_deck_summary(deck, card_count, viewer_count))

    return ApiResponseBuilder.ok().data(result).meta(
        total_count=len(result),
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    ).build()


@router.get("/user/{user_id}/dashboard", response_model=ApiResponse[Dict[str, List[DeckSummary]]])
def get_user_decks(user_id: UUID, db: Session = Depends(get_db)):
    """Get user's owned and shared decks for dashboard."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Verify user exists
    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Get owned decks
    owned_decks = deck_dao.get_by_owner(user_id, limit=100)
    owned_summaries = []
    for deck in owned_decks:
        card_count = card_dao.count_by_deck(deck.deck_id)
        viewer_count = len(viewer_dao.get_viewer_ids(deck.deck_id))
        owned_summaries.append(EntitySerializer.serialize_deck_summary(deck, card_count, viewer_count))

    # Get shared decks
    shared_decks = deck_dao.get_shared_with_user(user_id, limit=100)
    shared_summaries = []
    for deck in shared_decks:
        card_count = card_dao.count_by_deck(deck.deck_id)
        viewer_count = len(viewer_dao.get_viewer_ids(deck.deck_id))
        shared_summaries.append(EntitySerializer.serialize_deck_summary(deck, card_count, viewer_count))

    dashboard_data = {
        "owned_decks": owned_summaries,
        "shared_decks": shared_summaries
    }

    return ApiResponseBuilder.ok().data(dashboard_data).build()


@router.patch("/{deck_id}", response_model=ApiResponse[Deck])
def update_deck(
    deck_id: UUID,
    deck_update: DeckUpdate,
    db: Session = Depends(get_db)
):
    """Update deck information."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Update deck
    update_dict = deck_update.model_dump(exclude_unset=True, exclude={"cards"})
    deck = deck_dao.update(deck_id, update_dict)

    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Get current cards and viewers
    cards = card_dao.get_by_deck(deck_id)
    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    deck_data = EntitySerializer.serialize_deck(deck, cards, viewer_ids)

    return ApiResponseBuilder.ok().data(deck_data).message("Deck updated successfully").build()


@router.delete("/{deck_id}", response_model=ApiResponse)
def delete_deck(deck_id: UUID, db: Session = Depends(get_db)):
    """Delete a deck (soft delete)."""
    deck_dao = DeckDAO(db)

    deck = deck_dao.soft_delete(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    return ApiResponseBuilder.ok().message("Deck deleted successfully").build()


@router.post("/bulk-delete", response_model=ApiResponse[Dict])
def bulk_delete_decks(
    request: BulkDeleteDecksRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple decks at once."""
    deck_dao = DeckDAO(db)

    success_count = 0
    failed_ids = []
    errors = []

    for deck_id_str in request.deck_ids:
        try:
            deck_id = UUID(deck_id_str)
            result = deck_dao.soft_delete(deck_id)
            if result:
                success_count += 1
            else:
                failed_ids.append(deck_id_str)
                errors.append(f"Deck {deck_id_str} not found")
        except Exception as e:
            failed_ids.append(deck_id_str)
            errors.append(f"Error deleting deck {deck_id_str}: {str(e)}")

    bulk_operation_data = {
        "success_count": success_count,
        "failure_count": len(failed_ids),
        "failed_ids": failed_ids,
        "errors": errors
    }

    return ApiResponseBuilder.ok().data(bulk_operation_data).message(f"Bulk delete completed: {success_count} successful, {len(failed_ids)} failed").build()


@router.post("/{deck_id}/toggle-public", response_model=ApiResponse[Deck])
def toggle_public_status(deck_id: UUID, db: Session = Depends(get_db)):
    """Toggle deck public/private status."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)
    viewer_dao = DeckViewerDAO(db)

    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Toggle is_public
    deck = deck_dao.update(deck_id, {"is_public": not deck.is_public})

    # Get cards and viewers
    cards = card_dao.get_by_deck(deck_id)
    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    deck_data = EntitySerializer.serialize_deck(deck, cards, viewer_ids)
    return ApiResponseBuilder.ok().data(deck_data).message(f"Deck is now {'public' if deck.is_public else 'private'}").build()

