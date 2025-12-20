"""SQLAlchemy ORM models for the database schema."""

import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, Text, DateTime,
    ForeignKey, Enum, Index, UniqueConstraint, CheckConstraint,
    text, JSON, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .database import Base


class GUID(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, str):
            return str(value)
        return str(value)


class RendererType(str, enum.Enum):
    """Content renderer types for cards."""
    STRING = "string"
    MARKDOWN = "markdown"
    ABC_JS = "abc_js"
    IMAGE = "image"
    LATEX = "latex"
    MERMAID = "mermaid"


class User(Base):
    __tablename__ = "users"

    user_id = Column(GUID(), primary_key=True, default=uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=True)
    preferences = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owned_decks = relationship("Deck", back_populates="owner", foreign_keys="[Deck.owner_id]")
    viewed_decks = relationship("DeckViewer", back_populates="viewer", foreign_keys="[DeckViewer.viewer_id]")
    uploaded_files = relationship("UploadedFile", back_populates="user")
    sent_invitations = relationship("DeckInvitation", back_populates="sender", foreign_keys="[DeckInvitation.sender_id]")
    content_reports = relationship("ContentReport", back_populates="reporter", foreign_keys="[ContentReport.reporter_id]")
    auth_tokens = relationship("AuthToken", back_populates="user")

    __table_args__ = (
        Index('idx_users_deleted_at', 'deleted_at', postgresql_where=(deleted_at == None)),
    )

    def serialize(self, owned_decks_count: int = 0, shared_decks_count: int = 0) -> Dict[str, Any]:
        """Serialize user to dictionary with deck counts."""
        return {
            "user_id": str(self.user_id),
            "email": self.email,
            "name": self.name,
            "preferences": self.preferences or {},
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owned_decks_count": owned_decks_count,
            "shared_decks_count": shared_decks_count
        }


class Deck(Base):
    __tablename__ = "decks"

    deck_id = Column(GUID(), primary_key=True, default=uuid4)
    owner_id = Column(GUID(), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    is_public = Column(Boolean, nullable=False, default=False, server_default=text("FALSE"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    owner = relationship("User", back_populates="owned_decks", foreign_keys=[owner_id])
    cards = relationship("Card", back_populates="deck", cascade="all, delete-orphan")
    viewers = relationship("DeckViewer", back_populates="deck", cascade="all, delete-orphan")
    invitations = relationship("DeckInvitation", back_populates="deck", cascade="all, delete-orphan")
    files = relationship("UploadedFile", back_populates="deck")
    reports = relationship("ContentReport", back_populates="deck", cascade="all, delete-orphan")
    moderation = relationship("DeckModeration", back_populates="deck", uselist=False, cascade="all, delete-orphan")
    statistics = relationship("DeckStatistics", back_populates="deck", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_decks_owner_id', 'owner_id'),
        Index('idx_decks_is_public', 'is_public', postgresql_where=(is_public == True)),
        Index('idx_decks_created_at', 'created_at', postgresql_ops={'created_at': 'DESC'}),
        Index('idx_decks_deleted_at', 'deleted_at', postgresql_where=(deleted_at == None)),
        Index('idx_decks_public_created', 'created_at', postgresql_where=text("is_public = TRUE AND deleted_at IS NULL")),
        Index('idx_decks_owner_not_deleted', 'owner_id', 'created_at', postgresql_where=(deleted_at == None)),
    )

    def serialize(self, cards: Optional[List['Card']] = None, viewers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Serialize deck with cards and viewers."""
        return {
            "deck_id": str(self.deck_id),
            "owner_id": str(self.owner_id),
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "cards": [card.serialize() for card in cards] if cards else [],
            "shared_with": [str(vid) for vid in viewers] if viewers else [],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def serialize_summary(self, card_count: int = 0, viewer_count: int = 0) -> Dict[str, Any]:
        """Serialize deck as summary with counts."""
        return {
            "deck_id": str(self.deck_id),
            "owner_id": str(self.owner_id),
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "card_count": card_count,
            "shared_with_count": viewer_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Card(Base):
    __tablename__ = "cards"

    card_id = Column(GUID(), primary_key=True, default=uuid4)
    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), nullable=False)
    front_content = Column(Text, nullable=False)
    back_content = Column(Text, nullable=False)
    front_renderer = Column(Enum(RendererType), nullable=False, default=RendererType.STRING, server_default=text("'string'"))
    back_renderer = Column(Enum(RendererType), nullable=False, default=RendererType.STRING, server_default=text("'string'"))
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    deck = relationship("Deck", back_populates="cards")

    __table_args__ = (
        Index('idx_cards_deck_id', 'deck_id'),
        Index('idx_cards_deck_position', 'deck_id', 'position'),
        UniqueConstraint('deck_id', 'position', name='idx_cards_unique_position'),
    )

    def serialize(self) -> Dict[str, Any]:
        """Serialize card to dictionary."""
        return {
            "card_id": str(self.card_id),
            "front_content": self.front_content,
            "back_content": self.back_content,
            "front_renderer": self.front_renderer,
            "back_renderer": self.back_renderer,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class DeckViewer(Base):
    __tablename__ = "deck_viewers"

    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), primary_key=True)
    viewer_id = Column(GUID(), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    granted_by = Column(GUID(), ForeignKey("users.user_id"), nullable=True)

    # Relationships
    deck = relationship("Deck", back_populates="viewers")
    viewer = relationship("User", back_populates="viewed_decks", foreign_keys=[viewer_id])
    granter = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        Index('idx_deck_viewers_viewer_id', 'viewer_id'),
        Index('idx_deck_viewers_deck_id', 'deck_id'),
        Index('idx_deck_viewers_viewer_deck', 'viewer_id', 'granted_at', postgresql_ops={'granted_at': 'DESC'}),
    )


class DeckInvitation(Base):
    __tablename__ = "deck_invitations"

    invitation_id = Column(GUID(), primary_key=True, default=uuid4)
    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(GUID(), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    message = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="sent", server_default=text("'sent'"))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    deck = relationship("Deck", back_populates="invitations")
    sender = relationship("User", back_populates="sent_invitations", foreign_keys=[sender_id])

    __table_args__ = (
        Index('idx_deck_invitations_recipient_email', 'recipient_email'),
        Index('idx_deck_invitations_deck_id', 'deck_id'),
        Index('idx_deck_invitations_status', 'status'),
        Index('idx_deck_invitations_expires_at', 'expires_at'),
    )


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    file_id = Column(GUID(), primary_key=True, default=uuid4)
    user_id = Column(GUID(), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="SET NULL"), nullable=True)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_url = Column(Text, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="uploaded_files")
    deck = relationship("Deck", back_populates="files")

    __table_args__ = (
        Index('idx_uploaded_files_user_id', 'user_id'),
        Index('idx_uploaded_files_deck_id', 'deck_id'),
        Index('idx_uploaded_files_deleted_at', 'deleted_at', postgresql_where=(deleted_at == None)),
    )


class ContentReport(Base):
    __tablename__ = "content_reports"

    report_id = Column(GUID(), primary_key=True, default=uuid4)
    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), nullable=False)
    reporter_id = Column(GUID(), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reason = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, default="pending", server_default=text("'pending'"))
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(GUID(), ForeignKey("users.user_id"), nullable=True)
    moderator_notes = Column(Text, nullable=True)

    # Relationships
    deck = relationship("Deck", back_populates="reports")
    reporter = relationship("User", back_populates="content_reports", foreign_keys=[reporter_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index('idx_content_reports_deck_id', 'deck_id'),
        Index('idx_content_reports_status', 'status'),
        Index('idx_content_reports_submitted_at', 'submitted_at', postgresql_ops={'submitted_at': 'DESC'}),
    )


class DeckModeration(Base):
    __tablename__ = "deck_moderation"

    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), primary_key=True)
    status = Column(String(20), nullable=False, default="approved", server_default=text("'approved'"))
    reports_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    last_reviewed = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(GUID(), ForeignKey("users.user_id"), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    deck = relationship("Deck", back_populates="moderation")
    reviewer = relationship("User")

    __table_args__ = (
        Index('idx_deck_moderation_status', 'status'),
    )


class AuthToken(Base):
    __tablename__ = "auth_tokens"

    token_id = Column(GUID(), primary_key=True, default=uuid4)
    user_id = Column(GUID(), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    token_type = Column(String(20), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="auth_tokens")

    __table_args__ = (
        Index('idx_auth_tokens_user_id', 'user_id'),
        Index('idx_auth_tokens_token_hash', 'token_hash'),
        Index('idx_auth_tokens_expires_at', 'expires_at'),
    )


class DeckStatistics(Base):
    __tablename__ = "deck_statistics"

    stat_id = Column(GUID(), primary_key=True, default=uuid4)
    deck_id = Column(GUID(), ForeignKey("decks.deck_id", ondelete="CASCADE"), nullable=False)
    view_count = Column(Integer, nullable=False, default=0, server_default=text("0"))
    unique_viewers = Column(Integer, nullable=False, default=0, server_default=text("0"))
    last_viewed_at = Column(DateTime(timezone=True), nullable=True)
    usage_data = Column(JSON, nullable=False, default={})
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    deck = relationship("Deck", back_populates="statistics")

    __table_args__ = (
        Index('idx_deck_statistics_deck_id', 'deck_id'),
        Index('idx_deck_statistics_view_count', 'view_count', postgresql_ops={'view_count': 'DESC'}),
    )

