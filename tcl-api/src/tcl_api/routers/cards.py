"""Card management router."""

from typing import List, Dict
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.services.card import CardService
from tcl_api.models.card import (
    CardCreate,
    CardUpdate,
    ReorderCardsRequest,
    Card
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.response import ApiResponse
router = APIRouter(prefix="/cards", tags=["cards"])


@router.post("/", response_model=ApiResponse[Card])
def create_card(
    card_data: CardCreate,
    deck_id: UUID = Query(..., description="Deck ID to add card to"),
    db: Session = Depends(get_db)
):
    """Create a new card in a deck."""
    card_service = CardService(db)

    card_response_data = card_service.create_card(
        deck_id=deck_id,
        front_content=card_data.front_content,
        back_content=card_data.back_content,
        front_renderer=card_data.front_renderer,
        back_renderer=card_data.back_renderer
    )

    return ApiResponseBuilder.created().data(card_response_data).message("Card created successfully").build()


@router.get("/{card_id}", response_model=ApiResponse[Card])
def get_card(card_id: UUID, db: Session = Depends(get_db)):
    """Get a specific card by ID."""
    card_service = CardService(db)

    card_data = card_service.get_card(card_id)

    return ApiResponseBuilder.ok().data(card_data).build()


@router.get("/deck/{deck_id}", response_model=ApiResponse[List[Card]])
def get_deck_cards(deck_id: UUID, db: Session = Depends(get_db)):
    """Get all cards in a deck, ordered by position."""
    card_service = CardService(db)

    cards_data = card_service.get_deck_cards(deck_id)

    return ApiResponseBuilder.ok().data(cards_data).build()


@router.patch("/{card_id}", response_model=ApiResponse[Card])
def update_card(
    card_id: UUID,
    card_update: CardUpdate,
    db: Session = Depends(get_db)
):
    card_service = CardService(db)

    update_dict = card_update.model_dump(exclude_unset=True)
    card_data = card_service.update_card(card_id, **update_dict)

    return ApiResponseBuilder.ok().data(card_data).message("Card updated successfully").build()


@router.delete("/{card_id}", response_model=ApiResponse)
def delete_card(card_id: UUID, db: Session = Depends(get_db)):
    """Delete a card from a deck."""
    card_service = CardService(db)

    card_service.delete_card(card_id)

    return ApiResponseBuilder.ok().message("Card deleted successfully").build()


@router.post("/deck/{deck_id}/reorder", response_model=ApiResponse)
def reorder_cards(
    deck_id: UUID,
    reorder_request: ReorderCardsRequest,
    db: Session = Depends(get_db)
):
    """Reorder cards in a deck."""
    card_service = CardService(db)

    count = card_service.reorder_cards(deck_id, reorder_request.card_order)

    return ApiResponseBuilder.ok().message(f"Reordered {count} cards successfully").build()


@router.post("/deck/{deck_id}/bulk-create", response_model=ApiResponse[List[Card]])
def bulk_create_cards(
    deck_id: UUID,
    cards_data: List[CardCreate],
    db: Session = Depends(get_db)
):
    card_service = CardService(db)

    cards_list = [card.model_dump() for card in cards_data]
    cards_response_data = card_service.bulk_create_cards(deck_id, cards_list)

    return ApiResponseBuilder.created().data(cards_response_data).message(f"Created {len(cards_response_data)} cards successfully").build()


@router.delete("/deck/{deck_id}/all", response_model=ApiResponse)
def delete_all_cards_in_deck(deck_id: UUID, db: Session = Depends(get_db)):
    card_service = CardService(db)

    count = card_service.delete_all_cards_in_deck(deck_id)

    return ApiResponseBuilder.ok().message(f"Deleted {count} cards from deck").build()

