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
    """Utility class for backward compatibility. Serialization methods are now on models."""
    pass



