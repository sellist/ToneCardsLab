"""Card management router."""

from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import CardDAO, DeckDAO
from tcl_api.models.card import (
    CardCreate,
    CardUpdate,
    ReorderCardsRequest,
    Card
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.response import ApiResponse
from tcl_api.models.base import EntitySerializer
router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("/", response_model=ApiResponse[Card])
def create_card(
    card_data: CardCreate,
    deck_id: UUID = Query(..., description="Deck ID to add card to"),
    db: Session = Depends(get_db)
):
    """Create a new card in a deck."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Get current card count for position
    card_count = card_dao.count_by_deck(deck_id)

    # Create card
    card_dict = {
        "deck_id": deck_id,
        "front_content": card_data.front_content,
        "back_content": card_data.back_content,
        "front_renderer": card_data.front_renderer,
        "back_renderer": card_data.back_renderer,
        "position": card_count  # Add at end
    }
    card = card_dao.create(card_dict)

    card_data = EntitySerializer.serialize_card(card)
    return ApiResponseBuilder.created().data(card_data).message("Card created successfully").build()


@router.get("/{card_id}", response_model=ApiResponse[Card])
def get_card(card_id: UUID, db: Session = Depends(get_db)):
    """Get a specific card by ID."""
    card_dao = CardDAO(db)
    card = card_dao.get_by_id(card_id)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    card_data = EntitySerializer.serialize_card(card)
    return ApiResponseBuilder.ok().data(card_data).build()


@router.get("/deck/{deck_id}", response_model=ApiResponse[List[Card]])
def get_deck_cards(deck_id: UUID, db: Session = Depends(get_db)):
    """Get all cards in a deck, ordered by position."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    cards = card_dao.get_by_deck(deck_id)
    cards_data = [EntitySerializer.serialize_card(card) for card in cards]

    return ApiResponseBuilder.ok().data(cards_data).build()


@router.patch("/{card_id}", response_model=ApiResponse[Card])
def update_card(
    card_id: UUID,
    card_update: CardUpdate,
    db: Session = Depends(get_db)
):
    card_dao = CardDAO(db)

    update_dict = card_update.model_dump(exclude_unset=True)
    card = card_dao.update(card_id, update_dict)

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    card_data = EntitySerializer.serialize_card(card)
    return ApiResponseBuilder.ok().data(card_data).message("Card updated successfully").build()


@router.delete("/{card_id}", response_model=ApiResponse)
def delete_card(card_id: UUID, db: Session = Depends(get_db)):
    """Delete a card from a deck."""
    card_dao = CardDAO(db)

    success = card_dao.delete(card_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

    return ApiResponseBuilder.ok().message("Card deleted successfully").build()


@router.post("/deck/{deck_id}/reorder", response_model=ApiResponse)
def reorder_cards(
    deck_id: UUID,
    reorder_request: ReorderCardsRequest,
    db: Session = Depends(get_db)
):
    """Reorder cards in a deck."""
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Verify all cards belong to this deck
    cards = card_dao.get_by_deck(deck_id)
    card_ids_in_deck = {str(card.card_id) for card in cards}

    for card_id_str in reorder_request.card_order:
        if card_id_str not in card_ids_in_deck:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Card {card_id_str} does not belong to this deck"
            )

    card_positions: Dict[UUID, int] = {}
    for position, card_id_str in enumerate(reorder_request.card_order):
        card_positions[UUID(card_id_str)] = position

    card_dao.reorder_cards(card_positions)

    return ApiResponseBuilder.ok().message(f"Reordered {len(reorder_request.card_order)} cards successfully").build()


@router.post("/deck/{deck_id}/bulk-create", response_model=ApiResponse[List[Card]])
def bulk_create_cards(
    deck_id: UUID,
    cards_data: List[CardCreate],
    db: Session = Depends(get_db)
):
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    current_count = card_dao.count_by_deck(deck_id)

    cards_to_create = []
    for i, card_data in enumerate(cards_data):
        cards_to_create.append({
            "deck_id": deck_id,
            "front_content": card_data.front_content,
            "back_content": card_data.back_content,
            "front_renderer": card_data.front_renderer,
            "back_renderer": card_data.back_renderer,
            "position": current_count + i
        })

    # Bulk create
    created_cards = card_dao.bulk_create(cards_to_create)
    cards_response_data = [EntitySerializer.serialize_card(card) for card in created_cards]

    return ApiResponseBuilder.created().data(cards_response_data).message(f"Created {len(created_cards)} cards successfully").build()


@router.delete("/deck/{deck_id}/all", response_model=ApiResponse)
def delete_all_cards_in_deck(deck_id: UUID, db: Session = Depends(get_db)):
    deck_dao = DeckDAO(db)
    card_dao = CardDAO(db)

    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    count = card_dao.delete_by_deck(deck_id)

    return ApiResponseBuilder.ok().message(f"Deleted {count} cards from deck").build()

