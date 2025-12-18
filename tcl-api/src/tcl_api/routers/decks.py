"""Deck management router."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import DeckDAO, UserDAO, CardDAO, DeckViewerDAO
from tcl_api.models.deck import (
    DeckCreate,
    DeckUpdate,
    DeckResponse,
    DeckSummaryResponse,
    DeckListResponse,
    BulkDeleteDecksRequest
)
from tcl_api.models.card import CardResponse
from tcl_api.models.common import SuccessResponse, BulkOperationResponse

router = APIRouter(prefix="/decks", tags=["decks"])


@router.post("/", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
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
            created_cards.append(CardResponse(
                card_id=str(card.card_id),
                front_content=card.front_content,
                back_content=card.back_content,
                front_renderer=card.front_renderer,
                back_renderer=card.back_renderer
            ))

    return DeckResponse(
        deck_id=str(deck.deck_id),
        owner_id=str(deck.owner_id),
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        cards=created_cards,
        shared_with=[],
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )


@router.get("/{deck_id}", response_model=DeckResponse)
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

    # Get cards
    cards = card_dao.get_by_deck(deck_id)
    card_responses = [
        CardResponse(
            card_id=str(card.card_id),
            front_content=card.front_content,
            back_content=card.back_content,
            front_renderer=card.front_renderer,
            back_renderer=card.back_renderer
        )
        for card in cards
    ]

    # Get viewers
    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    return DeckResponse(
        deck_id=str(deck.deck_id),
        owner_id=str(deck.owner_id),
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        cards=card_responses,
        shared_with=[str(vid) for vid in viewer_ids],
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )


@router.get("/", response_model=List[DeckSummaryResponse])
def list_decks(
    owner_id: Optional[UUID] = None,
    is_public: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List decks with filtering and pagination."""
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

        result.append(DeckSummaryResponse(
            deck_id=str(deck.deck_id),
            owner_id=str(deck.owner_id),
            title=deck.title,
            description=deck.description,
            is_public=deck.is_public,
            card_count=card_count,
            shared_with_count=viewer_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at
        ))

    return result


@router.get("/user/{user_id}/dashboard", response_model=DeckListResponse)
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
        owned_summaries.append(DeckSummaryResponse(
            deck_id=str(deck.deck_id),
            owner_id=str(deck.owner_id),
            title=deck.title,
            description=deck.description,
            is_public=deck.is_public,
            card_count=card_count,
            shared_with_count=viewer_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at
        ))

    # Get shared decks
    shared_decks = deck_dao.get_shared_with_user(user_id, limit=100)
    shared_summaries = []
    for deck in shared_decks:
        card_count = card_dao.count_by_deck(deck.deck_id)
        viewer_count = len(viewer_dao.get_viewer_ids(deck.deck_id))
        shared_summaries.append(DeckSummaryResponse(
            deck_id=str(deck.deck_id),
            owner_id=str(deck.owner_id),
            title=deck.title,
            description=deck.description,
            is_public=deck.is_public,
            card_count=card_count,
            shared_with_count=viewer_count,
            created_at=deck.created_at,
            updated_at=deck.updated_at
        ))

    return DeckListResponse(
        owned_decks=owned_summaries,
        shared_decks=shared_summaries
    )


@router.patch("/{deck_id}", response_model=DeckResponse)
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

    # Get current cards
    cards = card_dao.get_by_deck(deck_id)
    card_responses = [
        CardResponse(
            card_id=str(card.card_id),
            front_content=card.front_content,
            back_content=card.back_content,
            front_renderer=card.front_renderer,
            back_renderer=card.back_renderer
        )
        for card in cards
    ]

    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    return DeckResponse(
        deck_id=str(deck.deck_id),
        owner_id=str(deck.owner_id),
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        cards=card_responses,
        shared_with=[str(vid) for vid in viewer_ids],
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )


@router.delete("/{deck_id}", response_model=SuccessResponse)
def delete_deck(deck_id: UUID, db: Session = Depends(get_db)):
    """Delete a deck (soft delete)."""
    deck_dao = DeckDAO(db)

    deck = deck_dao.soft_delete(deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    return SuccessResponse(
        success=True,
        message="Deck deleted successfully"
    )


@router.post("/bulk-delete", response_model=BulkOperationResponse)
def bulk_delete_decks(
    request: BulkDeleteDecksRequest,
    db: Session = Depends(get_db)
):
    """Delete multiple decks at once."""
    deck_dao = DeckDAO(db)

    success_count = 0
    failed_ids = []
    errors = []

    for deck_id in request.deck_ids:
        try:
            result = deck_dao.soft_delete(deck_id)
            if result:
                success_count += 1
            else:
                failed_ids.append(str(deck_id))
                errors.append(f"Deck {deck_id} not found")
        except Exception as e:
            failed_ids.append(str(deck_id))
            errors.append(f"Error deleting deck {deck_id}: {str(e)}")

    return BulkOperationResponse(
        success_count=success_count,
        failure_count=len(failed_ids),
        failed_ids=failed_ids,
        errors=errors
    )


@router.post("/{deck_id}/toggle-public", response_model=DeckResponse)
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

    cards = card_dao.get_by_deck(deck_id)
    card_responses = [
        CardResponse(
            card_id=str(card.card_id),
            front_content=card.front_content,
            back_content=card.back_content,
            front_renderer=card.front_renderer,
            back_renderer=card.back_renderer
        )
        for card in cards
    ]

    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    return DeckResponse(
        deck_id=str(deck.deck_id),
        owner_id=str(deck.owner_id),
        title=deck.title,
        description=deck.description,
        is_public=deck.is_public,
        cards=card_responses,
        shared_with=[str(vid) for vid in viewer_ids],
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )

