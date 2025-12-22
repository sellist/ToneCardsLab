"""Deck management router."""

from typing import Optional, List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.models.dto import DeckCreate, DeckSummary, DeckUpdate, BulkDeleteDecksRequest
from tcl_api.models.entities import Deck
from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import DeckDAO, UserDAO, CardDAO, DeckViewerDAO
from tcl_api.services.deck import DeckService

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
    deck_service = DeckService(db)
    user_dao = UserDAO(db)

    owner = user_dao.get_by_id(owner_id)
    if not owner or owner.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner user not found"
        )

    deck_dict = {
        "owner_id": owner_id,
        "title": deck_data.title,
        "description": deck_data.description,
        "is_public": deck_data.is_public
    }
    deck = deck_service.deck_dao.create(deck_dict)

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
            card = deck_service.card_dao.create(card_dict)
            created_cards.append(card)

    deck_response_data = deck.serialize(created_cards, [])

    return ApiResponseBuilder.created().data(deck_response_data).message("Deck created successfully").build()


@router.get("/{deck_id}", response_model=ApiResponse[Deck])
def get_deck(deck_id: UUID, db: Session = Depends(get_db)):
    """Get full deck details including all cards."""
    deck_service = DeckService(db)

    deck_data = deck_service.get_deck_with_permission(deck_id)

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
    deck_service = DeckService(db)
    deck_dao = DeckDAO(db)

    if search:
        decks = deck_dao.search_decks(
            query=search,
            owner_id=owner_id,
            is_public=is_public,
            skip=skip,
            limit=limit
        )
    elif owner_id:
        decks_data = deck_service.get_owned_decks(owner_id, skip=skip, limit=limit)
        return ApiResponseBuilder.ok().data(decks_data).meta(
            total_count=len(decks_data),
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        ).build()
    elif is_public:
        decks_data = deck_service.get_public_decks(skip=skip, limit=limit)
        return ApiResponseBuilder.ok().data(decks_data).meta(
            total_count=len(decks_data),
            page=skip // limit + 1 if limit > 0 else 1,
            page_size=limit
        ).build()
    else:
        decks = deck_dao.get_multi(skip=skip, limit=limit)

    result = []
    for deck in decks:
        if deck.deleted_at:
            continue

        result.append(deck.get_summary())

    return ApiResponseBuilder.ok().data(result).meta(
        total_count=len(result),
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit
    ).build()


@router.get("/user/{user_id}/dashboard", response_model=ApiResponse[Dict[str, List[DeckSummary]]])
def get_user_decks(user_id: UUID, db: Session = Depends(get_db)):
    """Get user's owned and shared decks for dashboard."""
    user_dao = UserDAO(db)
    deck_service = DeckService(db)

    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    owned_decks = deck_service.get_owned_decks(user_id, limit=100)
    accessible_decks = deck_service.get_accessible_decks(user_id, limit=100)

    shared_decks = [deck for deck in accessible_decks if deck['owner_id'] != user_id]

    dashboard_data = {
        "owned_decks": owned_decks,
        "shared_decks": shared_decks
    }

    return ApiResponseBuilder.ok().data(dashboard_data).build()


@router.patch("/{deck_id}", response_model=ApiResponse[Deck])
def update_deck(
    deck_id: UUID,
    deck_update: DeckUpdate,
    db: Session = Depends(get_db)
):
    deck_service = DeckService(db)

    update_dict = deck_update.model_dump(exclude_unset=True, exclude={"cards"})
    deck = deck_service.deck_dao.update(deck_id, update_dict)

    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    cards = deck_service.card_dao.get_by_deck(deck_id)
    viewer_ids = deck_service.deckviewer_dao.get_viewer_ids(deck_id)

    deck_data = deck.serialize(cards, viewer_ids)

    return ApiResponseBuilder.ok().data(deck_data).message("Deck updated successfully").build()


@router.delete("/{deck_id}", response_model=ApiResponse)
def delete_deck(deck_id: UUID, db: Session = Depends(get_db)):
    deck_service = DeckService(db)

    deck = deck_service.deck_dao.soft_delete(deck_id)
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
    deck_service = DeckService(db)

    success_count = 0
    failed_ids = []
    errors = []

    for deck_id_str in request.deck_ids:
        try:
            deck_id = UUID(deck_id_str)
            result = deck_service.deck_dao.soft_delete(deck_id)
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
    deck_service = DeckService(db)

    deck = deck_service.deck_dao.update(deck_id, {"is_public": not deck.is_public})

    cards = deck_service.card_dao.get_by_deck(deck_id)
    viewer_ids = deck_service.deckviewer_dao.get_viewer_ids(deck_id)

    deck_data = deck.serialize(cards, viewer_ids)
    return ApiResponseBuilder.ok().data(deck_data).message(f"Deck is now {'public' if deck.is_public else 'private'}").build()

