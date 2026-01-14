"""Card management service."""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from tcl_api.config import get_logger
from tcl_api.internal.injectors import get_dao, initialize_dao_factory
from tcl_api.models.entities import Card, Deck
from tcl_api.models.dto import CardRead
from tcl_api.models.mappers import card_to_read


@get_dao(Card)
@get_dao(Deck)
class CardService:
    card_dao: 'CardDAO'
    deck_dao: 'DeckDAO'

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("services.card")
        initialize_dao_factory(db)

    def _check_deck_exists(self, deck_id: UUID) -> Deck:
        deck = self.deck_dao.get_by_id(deck_id)
        if not deck or deck.deleted_at:
            self.logger.warning(f"Deck not found or deleted: {deck_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )
        return deck

    def _check_card_exists(self, card_id: UUID) -> Card:
        card = self.card_dao.get_by_id(card_id)
        if not card:
            self.logger.warning(f"Card not found: {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        return card

    def create_card(
        self,
        deck_id: UUID,
        front_content: str,
        back_content: str,
        front_renderer: Optional[str] = None,
        back_renderer: Optional[str] = None
    ) -> CardRead:
        """Create a new card in a deck."""
        self.logger.debug(f"Creating card in deck {deck_id}")

        self._check_deck_exists(deck_id)

        card_count = self.card_dao.count_by_deck(deck_id)

        card_dict = {
            "deck_id": deck_id,
            "front_content": front_content,
            "back_content": back_content,
            "front_renderer": front_renderer,
            "back_renderer": back_renderer,
            "position": card_count
        }

        card = self.card_dao.create(card_dict)

        self.logger.info(f"Successfully created card {card.card_id}")

        return card_to_read(card)

    def get_card(self, card_id: UUID) -> CardRead:
        self.logger.debug(f"Retrieving card: {card_id}")

        card = self._check_card_exists(card_id)

        self.logger.info(f"Retrieved card: {card_id}")

        return card_to_read(card)

    def get_cards_by_deck(self, deck_id: UUID) -> List[CardRead]:
        self.logger.debug(f"Retrieving cards for deck: {deck_id}")

        self._check_deck_exists(deck_id)

        cards = self.card_dao.get_by_deck_id(deck_id)

        self.logger.info(f"Retrieved {len(cards)} cards for deck {deck_id}")

        return [card_to_read(card) for card in cards]

    def update_card(
        self,
        card_id: UUID,
        **update_data
    ) -> CardRead:
        """Update a card."""
        self.logger.debug(f"Updating card {card_id}")

        card = self.card_dao.update(card_id, update_data)

        if not card:
            self.logger.warning(f"Card not found for update: {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )

        self.logger.info(f"Successfully updated card {card_id}")

        return card_to_read(card)

    def delete_card(self, card_id: UUID) -> bool:
        """Delete a card."""
        self.logger.debug(f"Deleting card {card_id}")

        success = self.card_dao.delete(card_id)

        if not success:
            self.logger.warning(f"Failed to delete card {card_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )

        self.logger.info(f"Successfully deleted card {card_id}")

        return True

    def reorder_cards(
        self,
        deck_id: UUID,
        card_order: List[str]
    ) -> int:
        """Reorder cards in a deck."""
        self.logger.debug(f"Reordering {len(card_order)} cards in deck {deck_id}")

        self._check_deck_exists(deck_id)

        cards = self.card_dao.get_by_deck(deck_id)
        card_ids_in_deck = {str(card.card_id) for card in cards}

        for card_id_str in card_order:
            if card_id_str not in card_ids_in_deck:
                self.logger.warning(f"Card {card_id_str} not found in deck {deck_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Card {card_id_str} does not belong to this deck"
                )

        card_positions: Dict[UUID, int] = {}
        for position, card_id_str in enumerate(card_order):
            card_positions[UUID(card_id_str)] = position

        self.card_dao.reorder_cards(card_positions)

        self.logger.info(f"Successfully reordered {len(card_order)} cards")

        return len(card_order)

    def bulk_create_cards(
        self,
        deck_id: UUID,
        cards_data: List[Dict[str, Any]]
    ) -> List[CardRead]:
        """Create multiple cards in a deck."""
        self.logger.debug(f"Bulk creating {len(cards_data)} cards in deck {deck_id}")

        self._check_deck_exists(deck_id)

        current_count = self.card_dao.count_by_deck(deck_id)

        cards_to_create = []
        for i, card_data in enumerate(cards_data):
            cards_to_create.append({
                "deck_id": deck_id,
                "front_content": card_data.get("front_content"),
                "back_content": card_data.get("back_content"),
                "front_renderer": card_data.get("front_renderer"),
                "back_renderer": card_data.get("back_renderer"),
                "position": current_count + i
            })

        created_cards = self.card_dao.bulk_create(cards_to_create)

        self.logger.info(f"Successfully created {len(created_cards)} cards")

        return [card_to_read(card) for card in created_cards]

    def delete_all_cards_in_deck(self, deck_id: UUID) -> int:
        """Delete all cards in a deck."""
        self.logger.debug(f"Deleting all cards in deck {deck_id}")

        self._check_deck_exists(deck_id)

        count = self.card_dao.delete_by_deck(deck_id)

        self.logger.info(f"Successfully deleted {count} cards from deck {deck_id}")

        return count

