"""
Unified SQLModel entities - single source of truth for database and API models.

Each model serves both as:
- SQLAlchemy ORM model for database operations (when table=True)
- Pydantic model for API request/response validation
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, Text, BigInteger, JSON, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import TypeDecorator


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, UUID):
            return value
        return UUID(value) if value else None


# ---------------------------------------------------------------------------
# enums
# ---------------------------------------------------------------------------

class RendererType(str, Enum):
    """Available content renderer types for cards."""
    STRING = "string"
    MARKDOWN = "markdown"
    ABC_JS = "abc_js"
    IMAGE = "image"
    LATEX = "latex"
    MERMAID = "mermaid"


# database models
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    """User account - both database table and API model."""
    __tablename__ = "users"

    user_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the user"
    )
    email: str = Field(
        max_length=255,
        index=True,
        sa_column_kwargs={"unique": True},
        description="User's email address"
    )
    name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="User's display name"
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        description="When the user was created"
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        description="When the user was last updated"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Soft delete timestamp"
    )

    # Relationships
    owned_decks: List["Deck"] = Relationship(
        back_populates="owner",
        sa_relationship_kwargs={"foreign_keys": "[Deck.owner_id]"}
    )
    viewed_decks: List["DeckViewer"] = Relationship(
        back_populates="viewer",
        sa_relationship_kwargs={"foreign_keys": "[DeckViewer.viewer_id]"}
    )
    uploaded_files: List["UploadedFile"] = Relationship(back_populates="user")
    sent_invitations: List["DeckInvitation"] = Relationship(
        back_populates="sender",
        sa_relationship_kwargs={"foreign_keys": "[DeckInvitation.sender_id]"}
    )
    content_reports: List["ContentReport"] = Relationship(
        back_populates="reporter",
        sa_relationship_kwargs={"foreign_keys": "[ContentReport.reporter_id]"}
    )
    auth_tokens: List["AuthToken"] = Relationship(back_populates="user")

    def serialize(self, owned_decks_count: int = 0, shared_decks_count: int = 0) -> Dict[str, Any]:
        """Serialize User for API response."""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owned_decks_count": owned_decks_count,
            "shared_decks_count": shared_decks_count,
        }


class Deck(SQLModel, table=True):
    """Flashcard deck - both database table and API model."""
    __tablename__ = "decks"

    deck_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the deck"
    )
    owner_id: UUID = Field(
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of the deck owner"
    )
    title: str = Field(
        max_length=200,
        min_length=1,
        description="Deck title"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Deck description"
    )
    is_public: bool = Field(
        default=False,
        sa_column_kwargs={"server_default": text("FALSE")},
        description="Whether deck is publicly accessible"
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        description="When the deck was created"
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        description="When the deck was last updated"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Soft delete timestamp"
    )

    # Relationships
    owner: Optional["User"] = Relationship(
        back_populates="owned_decks",
        sa_relationship_kwargs={"foreign_keys": "[Deck.owner_id]"}
    )
    cards: List["Card"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    viewers: List["DeckViewer"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    invitations: List["DeckInvitation"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    files: List["UploadedFile"] = Relationship(back_populates="deck")
    reports: List["ContentReport"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    moderation: Optional["DeckModeration"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    statistics: Optional["DeckStatistics"] = Relationship(
        back_populates="deck",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )

    def serialize(self, cards: Optional[List["Card"]] = None, viewer_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Serialize Deck for API response."""
        card_list = cards or []
        viewer_list = viewer_ids or []
        return {
            "deck_id": self.deck_id,
            "owner_id": self.owner_id,
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "cards": [card.serialize() for card in card_list],
            "shared_with": viewer_list,
            "card_count": len(card_list),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Card(SQLModel, table=True):
    """Flashcard within a deck - both database table and API model."""
    __tablename__ = "cards"

    card_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the card"
    )
    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the parent deck"
    )
    front_content: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Content to display on front of card"
    )
    back_content: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Content to display on back of card"
    )
    front_renderer: RendererType = Field(
        default=RendererType.STRING,
        sa_column_kwargs={"server_default": text("'string'")},
        description="Renderer type for front content"
    )
    back_renderer: RendererType = Field(
        default=RendererType.STRING,
        sa_column_kwargs={"server_default": text("'string'")},
        description="Renderer type for back content"
    )
    position: int = Field(
        default=0,
        description="Card position within the deck"
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        description="When the card was created"
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        description="When the card was last updated"
    )

    # Relationships
    deck: Optional["Deck"] = Relationship(back_populates="cards")

    __table_args__ = (
        UniqueConstraint('deck_id', 'position', name='idx_cards_unique_position'),
    )

    def serialize(self) -> Dict[str, Any]:
        """Serialize Card for API response."""
        return {
            "card_id": self.card_id,
            "front_content": self.front_content,
            "back_content": self.back_content,
            "front_renderer": self.front_renderer.value if isinstance(self.front_renderer, RendererType) else self.front_renderer,
            "back_renderer": self.back_renderer.value if isinstance(self.back_renderer, RendererType) else self.back_renderer,
            "position": self.position,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class DeckViewer(SQLModel, table=True):
    """Shared deck viewer access - database junction table."""
    __tablename__ = "deck_viewers"

    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        primary_key=True,
        sa_type=GUID(),
        description="UUID of the shared deck"
    )
    viewer_id: UUID = Field(
        foreign_key="users.user_id",
        primary_key=True,
        sa_type=GUID(),
        description="UUID of the viewer"
    )
    granted_at: datetime = Field(
        default_factory=utcnow,
        description="When access was granted"
    )
    granted_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of user who granted access"
    )

    # Relationships
    deck: Optional["Deck"] = Relationship(back_populates="viewers")
    viewer: Optional["User"] = Relationship(
        back_populates="viewed_decks",
        sa_relationship_kwargs={"foreign_keys": "[DeckViewer.viewer_id]"}
    )
    granter: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[DeckViewer.granted_by]"}
    )


class DeckInvitation(SQLModel, table=True):
    """Deck sharing invitation - database table."""
    __tablename__ = "deck_invitations"

    invitation_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the invitation"
    )
    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the deck being shared"
    )
    sender_id: UUID = Field(
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of the sender"
    )
    recipient_email: str = Field(
        max_length=255,
        index=True,
        description="Email address of the recipient"
    )
    message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional invitation message"
    )
    status: str = Field(
        default="sent",
        max_length=20,
        sa_column_kwargs={"server_default": text("'sent'")},
        description="Invitation status"
    )
    expires_at: datetime = Field(description="When the invitation expires")
    created_at: datetime = Field(
        default_factory=utcnow,
        description="When the invitation was created"
    )
    accepted_at: Optional[datetime] = Field(
        default=None,
        description="When the invitation was accepted"
    )

    # Relationships
    deck: Optional["Deck"] = Relationship(back_populates="invitations")
    sender: Optional["User"] = Relationship(
        back_populates="sent_invitations",
        sa_relationship_kwargs={"foreign_keys": "[DeckInvitation.sender_id]"}
    )

    def serialize(self) -> Dict[str, Any]:
        """Serialize DeckInvitation for API response."""
        return {
            "invitation_id": self.invitation_id,
            "deck_id": self.deck_id,
            "sender_id": self.sender_id,
            "recipient_email": self.recipient_email,
            "message": self.message,
            "status": self.status,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "accepted_at": self.accepted_at,
        }


class UploadedFile(SQLModel, table=True):
    """User uploaded file metadata - database table."""
    __tablename__ = "uploaded_files"

    file_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the file"
    )
    user_id: UUID = Field(
        foreign_key="users.user_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the file owner"
    )
    deck_id: Optional[UUID] = Field(
        default=None,
        foreign_key="decks.deck_id",
        sa_type=GUID(),
        index=True,
        description="Optional associated deck ID"
    )
    file_name: str = Field(
        max_length=255,
        description="Original filename"
    )
    file_size: int = Field(
        sa_column=Column(BigInteger, nullable=False),
        description="File size in bytes"
    )
    mime_type: str = Field(
        max_length=100,
        description="MIME type of the file"
    )
    file_url: str = Field(
        sa_column=Column(Text, nullable=False),
        description="URL to access the file"
    )
    uploaded_at: datetime = Field(
        default_factory=utcnow,
        description="When the file was uploaded"
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        description="Soft delete timestamp"
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="uploaded_files")
    deck: Optional["Deck"] = Relationship(back_populates="files")

    def serialize(self) -> Dict[str, Any]:
        """Serialize UploadedFile for API response."""
        return {
            "file_id": self.file_id,
            "file_url": self.file_url,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "uploaded_at": self.uploaded_at,
            "deck_id": self.deck_id,
        }


class ContentReport(SQLModel, table=True):
    """Content moderation report - database table."""
    __tablename__ = "content_reports"

    report_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the report"
    )
    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the reported deck"
    )
    reporter_id: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of the reporter"
    )
    reason: str = Field(
        max_length=100,
        description="Report reason"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Detailed description"
    )
    status: str = Field(
        default="pending",
        max_length=20,
        sa_column_kwargs={"server_default": text("'pending'")},
        description="Report status"
    )
    submitted_at: datetime = Field(
        default_factory=utcnow,
        description="When the report was submitted"
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="When the report was reviewed"
    )
    reviewed_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of the reviewer"
    )
    moderator_notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Internal moderator notes"
    )

    # Relationships
    deck: Optional["Deck"] = Relationship(back_populates="reports")
    reporter: Optional["User"] = Relationship(
        back_populates="content_reports",
        sa_relationship_kwargs={"foreign_keys": "[ContentReport.reporter_id]"}
    )
    reviewer: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ContentReport.reviewed_by]"}
    )


class DeckModeration(SQLModel, table=True):
    """Deck moderation status - database table."""
    __tablename__ = "deck_moderation"

    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        primary_key=True,
        sa_type=GUID(),
        description="UUID of the deck"
    )
    status: str = Field(
        default="approved",
        max_length=20,
        sa_column_kwargs={"server_default": text("'approved'")},
        description="Moderation status"
    )
    reports_count: int = Field(
        default=0,
        sa_column_kwargs={"server_default": text("0")},
        description="Number of reports"
    )
    last_reviewed: Optional[datetime] = Field(
        default=None,
        description="When last reviewed"
    )
    reviewed_by: Optional[UUID] = Field(
        default=None,
        foreign_key="users.user_id",
        sa_type=GUID(),
        description="UUID of the reviewer"
    )
    notes: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Moderator notes"
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        description="When last updated"
    )

    deck: Optional["Deck"] = Relationship(back_populates="moderation")
    reviewer: Optional["User"] = Relationship()


class AuthToken(SQLModel, table=True):
    __tablename__ = "auth_tokens"

    token_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier for the token"
    )
    user_id: UUID = Field(
        foreign_key="users.user_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the token owner"
    )
    token_hash: str = Field(
        max_length=255,
        sa_column_kwargs={"unique": True},
        description="Hashed token value"
    )
    token_type: str = Field(
        max_length=20,
        description="Token type (access, refresh)"
    )
    expires_at: datetime = Field(
        index=True,
        description="Token expiration time"
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        description="When token was revoked"
    )
    created_at: datetime = Field(
        default_factory=utcnow,
        description="When the token was created"
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="auth_tokens")


class DeckStatistics(SQLModel, table=True):
    __tablename__ = "deck_statistics"

    stat_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=GUID(),
        description="Unique identifier"
    )
    deck_id: UUID = Field(
        foreign_key="decks.deck_id",
        sa_type=GUID(),
        index=True,
        description="UUID of the deck"
    )
    view_count: int = Field(
        default=0,
        sa_column_kwargs={"server_default": text("0")},
        description="Total view count"
    )
    unique_viewers: int = Field(
        default=0,
        sa_column_kwargs={"server_default": text("0")},
        description="Unique viewer count"
    )
    last_viewed_at: Optional[datetime] = Field(
        default=None,
        description="Last view timestamp"
    )
    usage_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, default={}),
        description="Additional usage statistics"
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        description="When last updated"
    )
    deck: Optional["Deck"] = Relationship(back_populates="statistics")
