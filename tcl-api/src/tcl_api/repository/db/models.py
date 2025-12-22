"""
Database models - re-exported from unified SQLModel entities.

This file exists for backward compatibility. All models are now defined
in tcl_api.models.entities using SQLModel (which combines SQLAlchemy + Pydantic).

Import models from tcl_api.models instead of this module.
"""

from tcl_api.models import (
    # Database table models
    User,
    Deck,
    Card,
    DeckViewer,
    DeckInvitation,
    UploadedFile,
    ContentReport,
    DeckModeration,
    AuthToken,
    DeckStatistics,

    # Enums
    RendererType,

    # Custom types
    GUID,
)

__all__ = [
    "User",
    "Deck",
    "Card",
    "DeckViewer",
    "DeckInvitation",
    "UploadedFile",
    "ContentReport",
    "DeckModeration",
    "AuthToken",
    "DeckStatistics",
    "RendererType",
    "GUID",
]
