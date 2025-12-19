"""Base model classes with export functionality."""

from typing import Dict, Any
from pydantic import BaseModel
from datetime import datetime


def _serialize_entity(entity: Any) -> Dict[str, Any]:
    """Serialize database entity to dictionary."""
    result = {}
    for key, value in entity.__dict__.items():
        if key.startswith('_'):  # Skip SQLAlchemy internal attributes
            continue
        if isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result


class ExportableModel(BaseModel):
    """Base model with export functionality."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary with proper serialization."""
        data = self.model_dump()
        return self._serialize_values(data)

    def _serialize_values(self, data: Any) -> Any:
        """Recursively serialize values for JSON compatibility."""
        if isinstance(data, dict):
            return {key: self._serialize_values(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._serialize_values(item) for item in data]
        elif hasattr(data, '__dict__'):  # Handle database entities
            return _serialize_entity(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data


class EntitySerializer:
    """Utility class for serializing database entities to dictionaries."""

    @staticmethod
    def serialize_deck(deck, cards=None, viewers=None) -> Dict[str, Any]:
        return {
            "deck_id": str(deck.deck_id),
            "owner_id": str(deck.owner_id),
            "title": deck.title,
            "description": deck.description,
            "is_public": deck.is_public,
            "cards": [EntitySerializer.serialize_card(card) for card in cards] if cards else [],
            "shared_with": [str(vid) for vid in viewers] if viewers else [],
            "created_at": deck.created_at,
            "updated_at": deck.updated_at
        }

    @staticmethod
    def serialize_card(card) -> Dict[str, Any]:
        return {
            "card_id": str(card.card_id),
            "front_content": card.front_content,
            "back_content": card.back_content,
            "front_renderer": card.front_renderer,
            "back_renderer": card.back_renderer,
            "created_at": card.created_at,
            "updated_at": card.updated_at
        }
    @staticmethod
    def serialize_deck_summary(deck, card_count=0, viewer_count=0) -> Dict[str, Any]:
        """Serialize a deck entity as summary."""
        return {
            "deck_id": str(deck.deck_id),
            "owner_id": str(deck.owner_id),
            "title": deck.title,
            "description": deck.description,
            "is_public": deck.is_public,
            "card_count": card_count,
            "shared_with_count": viewer_count,
            "created_at": deck.created_at,
            "updated_at": deck.updated_at
        }



