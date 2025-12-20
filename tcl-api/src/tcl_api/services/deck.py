from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from tcl_api.config import get_logger
from tcl_api.internal.injectors import get_dao, initialize_dao_factory
from tcl_api.repository.db.models import Deck, Card, DeckViewer


@get_dao(Deck)
@get_dao(Card)
@get_dao(DeckViewer)
class DeckService:
    # type hints for injected DAOs to help IDE
    deck_dao: 'DeckDAO'
    card_dao: 'CardDAO'
    deckviewer_dao: 'DeckViewerDAO'

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("services.deck")

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

    def _has_permission(self, deck: Deck, user_id: UUID) -> bool:
        if deck.owner_id == user_id:
            return True

        if deck.is_public:
            return True

        if self.deckviewer_dao.is_viewer(deck.deck_id, user_id):
            return True

        return False

    def get_deck_with_permission(
        self,
        deck_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        self.logger.debug(f"Retrieving deck {deck_id} for user {user_id}")

        deck = self._check_deck_exists(deck_id)

        if not deck.is_public and user_id is None:
            self.logger.warning(f"Anonymous access denied to private deck: {deck_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to access this deck"
            )

        if not deck.is_public and not self._has_permission(deck, user_id):
            self.logger.warning(
                f"User {user_id} denied access to deck {deck_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this deck"
            )

        cards = self.card_dao.get_by_deck(deck_id)
        viewer_ids = self.deckviewer_dao.get_viewer_ids(deck_id)

        self.logger.info(f"Successfully retrieved deck {deck_id} for user {user_id}")

        return deck.serialize(cards, viewer_ids)

    def is_owner(self, deck_id: UUID, user_id: UUID) -> bool:
        deck = self._check_deck_exists(deck_id)
        return deck.owner_id == user_id

    def has_view_access(self, deck_id: UUID, user_id: Optional[UUID] = None) -> bool:
        try:
            deck = self._check_deck_exists(deck_id)

            if deck.is_public:
                return True

            if user_id is None:
                return False

            return self._has_permission(deck, user_id)
        except HTTPException:
            return False

    def get_accessible_decks(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Retrieving accessible decks for user {user_id}")

        owned = self.deck_dao.get_by_owner(user_id, skip=0, limit=limit)

        shared = self.deck_dao.get_shared_with_user(user_id, skip=0, limit=limit)

        public = self.deck_dao.get_public_decks(skip=0, limit=limit)

        all_decks = {deck.deck_id: deck for deck in owned + shared + public}
        decks = list(all_decks.values())

        result = decks[skip:skip + limit]

        self.logger.info(
            f"Retrieved {len(result)} accessible decks for user {user_id}"
        )

        # Convert to deck summaries with card counts
        deck_summaries = []
        for deck in result:
            card_count = self.card_dao.count_by_deck(deck.deck_id) if hasattr(self.card_dao, 'count_by_deck') else 0
            viewer_count = len(self.deckviewer_dao.get_viewer_ids(deck.deck_id))
            deck_summaries.append(deck.serialize_summary(card_count, viewer_count))

        return deck_summaries

    def get_public_decks(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Retrieving public decks")

        public_decks = self.deck_dao.get_public_decks(skip=skip, limit=limit)

        self.logger.info(f"Retrieved {len(public_decks)} public decks")

        # Convert to deck summaries with card counts
        deck_summaries = []
        for deck in public_decks:
            card_count = self.card_dao.count_by_deck(deck.deck_id) if hasattr(self.card_dao, 'count_by_deck') else 0
            viewer_count = len(self.deckviewer_dao.get_viewer_ids(deck.deck_id))
            deck_summaries.append(deck.serialize_summary(card_count, viewer_count))

        return deck_summaries

    def get_owned_decks(
        self,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Retrieving decks owned by user {owner_id}")

        owned_decks = self.deck_dao.get_by_owner(owner_id, skip=skip, limit=limit)

        self.logger.info(f"Retrieved {len(owned_decks)} owned decks for user {owner_id}")

        # Convert to deck summaries with card counts
        deck_summaries = []
        for deck in owned_decks:
            card_count = self.card_dao.count_by_deck(deck.deck_id) if hasattr(self.card_dao, 'count_by_deck') else 0
            viewer_count = len(self.deckviewer_dao.get_viewer_ids(deck.deck_id))
            deck_summaries.append(deck.serialize_summary(card_count, viewer_count))

        return deck_summaries

    def get_premade_decks(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        self.logger.debug(f"Retrieving premade decks")

        premade_decks = self.deck_dao.get_premade_decks(skip=skip, limit=limit)

        self.logger.info(f"Retrieved {len(premade_decks)} premade decks")

        # Convert to deck summaries with card counts
        deck_summaries = []
        for deck in premade_decks:
            card_count = self.card_dao.count_by_deck(deck.deck_id) if hasattr(self.card_dao, 'count_by_deck') else 0
            viewer_count = len(self.deckviewer_dao.get_viewer_ids(deck.deck_id))
            deck_summaries.append(deck.serialize_summary(card_count, viewer_count))

        return deck_summaries

