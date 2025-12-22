"""Concrete DAO implementations for database entities."""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from .base import BaseDAO
from .models import User, Deck, Card, DeckViewer, DeckInvitation, UploadedFile, ContentReport


def utcnow() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class UserDAO(BaseDAO[User, dict, dict]):
    """Data Access Object for User operations."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        stmt = select(User).where(User.email == email).where(User.deleted_at.is_(None))
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active (non-deleted) users."""
        stmt = select(User).where(User.deleted_at.is_(None)).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def search_by_name_or_email(self, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """Search users by name or email."""
        search_pattern = f"%{query}%"
        stmt = (
            select(User)
            .where(User.deleted_at.is_(None))
            .where(or_(
                User.name.ilike(search_pattern),
                User.email.ilike(search_pattern)
            ))
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())


class DeckDAO(BaseDAO[Deck, dict, dict]):
    """Data Access Object for Deck operations."""

    def __init__(self, db: Session):
        super().__init__(Deck, db)

    def get_by_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[Deck]:
        """Get all decks owned by a user."""
        stmt = (
            select(Deck)
            .where(Deck.owner_id == owner_id)
            .where(Deck.deleted_at.is_(None))
            .order_by(Deck.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_public_decks(self, skip: int = 0, limit: int = 100) -> List[Deck]:
        """Get all public decks."""
        stmt = (
            select(Deck)
            .where(Deck.is_public == True)
            .where(Deck.deleted_at.is_(None))
            .order_by(Deck.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_shared_with_user(self, viewer_id: UUID, skip: int = 0, limit: int = 100) -> List[Deck]:
        """Get decks shared with a specific user."""
        stmt = (
            select(Deck)
            .join(DeckViewer, Deck.deck_id == DeckViewer.deck_id)
            .where(DeckViewer.viewer_id == viewer_id)
            .where(Deck.deleted_at.is_(None))
            .order_by(DeckViewer.granted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def search_decks(
        self,
        query: str,
        owner_id: Optional[UUID] = None,
        is_public: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Deck]:
        """Search decks by title or description."""
        search_pattern = f"%{query}%"
        stmt = select(Deck).where(Deck.deleted_at.is_(None))

        stmt = stmt.where(or_(
            Deck.title.ilike(search_pattern),
            Deck.description.ilike(search_pattern)
        ))

        if owner_id:
            stmt = stmt.where(Deck.owner_id == owner_id)

        if is_public is not None:
            stmt = stmt.where(Deck.is_public == is_public)

        stmt = stmt.order_by(Deck.created_at.desc()).offset(skip).limit(limit)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def count_by_owner(self, owner_id: UUID) -> int:
        """Count decks owned by a user."""
        return self.count(filters={"owner_id": owner_id, "deleted_at": None})


class CardDAO(BaseDAO[Card, dict, dict]):
    """Data Access Object for Card operations."""

    def __init__(self, db: Session):
        super().__init__(Card, db)

    def get_by_deck(self, deck_id: UUID) -> List[Card]:
        """Get all cards in a deck, ordered by position."""
        stmt = (
            select(Card)
            .where(Card.deck_id == deck_id)
            .order_by(Card.position)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def reorder_cards(self, card_positions: dict[UUID, int]) -> None:
        """Update card positions in bulk."""
        for card_id, position in card_positions.items():
            card = self.get_by_id(card_id)
            if card:
                card.position = position
        self.db.commit()

    def count_by_deck(self, deck_id: UUID) -> int:
        """Count cards in a deck."""
        return self.count(filters={"deck_id": deck_id})

    def delete_by_deck(self, deck_id: UUID) -> int:
        """Delete all cards in a deck."""
        cards = self.get_by_deck(deck_id)
        count = len(cards)
        for card in cards:
            self.db.delete(card)
        self.db.commit()
        return count


class DeckViewerDAO(BaseDAO[DeckViewer, dict, dict]):
    """Data Access Object for DeckViewer operations."""

    def __init__(self, db: Session):
        super().__init__(DeckViewer, db)

    def add_viewer(
        self,
        deck_id: UUID,
        viewer_id: UUID,
        granted_by: Optional[UUID] = None
    ) -> DeckViewer:
        """Add a viewer to a deck."""
        viewer = DeckViewer(
            deck_id=deck_id,
            viewer_id=viewer_id,
            granted_by=granted_by
        )
        self.db.add(viewer)
        self.db.commit()
        self.db.refresh(viewer)
        return viewer

    def remove_viewer(self, deck_id: UUID, viewer_id: UUID) -> bool:
        """Remove a viewer from a deck."""
        stmt = select(DeckViewer).where(
            and_(
                DeckViewer.deck_id == deck_id,
                DeckViewer.viewer_id == viewer_id
            )
        )
        result = self.db.execute(stmt)
        viewer = result.scalar_one_or_none()

        if viewer:
            self.db.delete(viewer)
            self.db.commit()
            return True
        return False

    def get_viewers(self, deck_id: UUID) -> List[DeckViewer]:
        """Get all viewers for a deck."""
        stmt = select(DeckViewer).where(DeckViewer.deck_id == deck_id)
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_viewer_ids(self, deck_id: UUID) -> List[UUID]:
        """Get viewer IDs for a deck."""
        viewers = self.get_viewers(deck_id)
        return [v.viewer_id for v in viewers]

    def is_viewer(self, deck_id: UUID, viewer_id: UUID) -> bool:
        """Check if a user is a viewer of a deck."""
        stmt = select(DeckViewer).where(
            and_(
                DeckViewer.deck_id == deck_id,
                DeckViewer.viewer_id == viewer_id
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none() is not None


class DeckInvitationDAO(BaseDAO[DeckInvitation, dict, dict]):
    """Data Access Object for DeckInvitation operations."""

    def __init__(self, db: Session):
        super().__init__(DeckInvitation, db)

    def get_pending_invitations(self, recipient_email: str) -> List[DeckInvitation]:
        """Get pending invitations for an email address."""
        stmt = (
            select(DeckInvitation)
            .where(DeckInvitation.recipient_email == recipient_email)
            .where(DeckInvitation.status == "sent")
            .where(DeckInvitation.expires_at > utcnow())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def accept_invitation(self, invitation_id: UUID) -> Optional[DeckInvitation]:
        """Mark an invitation as accepted."""
        invitation = self.get_by_id(invitation_id)
        if invitation and invitation.status == "sent":
            invitation.status = "accepted"
            invitation.accepted_at = utcnow()
            self.db.commit()
            self.db.refresh(invitation)
        return invitation

    def expire_old_invitations(self) -> int:
        """Mark expired invitations as expired."""
        stmt = (
            select(DeckInvitation)
            .where(DeckInvitation.status == "sent")
            .where(DeckInvitation.expires_at <= utcnow())
        )
        result = self.db.execute(stmt)
        invitations = list(result.scalars().all())

        for invitation in invitations:
            invitation.status = "expired"

        self.db.commit()
        return len(invitations)


class UploadedFileDAO(BaseDAO[UploadedFile, dict, dict]):
    """Data Access Object for UploadedFile operations."""

    def __init__(self, db: Session):
        super().__init__(UploadedFile, db)

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[UploadedFile]:
        """Get all files uploaded by a user."""
        stmt = (
            select(UploadedFile)
            .where(UploadedFile.user_id == user_id)
            .where(UploadedFile.deleted_at.is_(None))
            .order_by(UploadedFile.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_by_deck(self, deck_id: UUID) -> List[UploadedFile]:
        """Get all files associated with a deck."""
        stmt = (
            select(UploadedFile)
            .where(UploadedFile.deck_id == deck_id)
            .where(UploadedFile.deleted_at.is_(None))
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_total_size_by_user(self, user_id: UUID) -> int:
        """Calculate total file size for a user."""
        files = self.get_by_user(user_id)
        return sum(f.file_size for f in files)


class ContentReportDAO(BaseDAO[ContentReport, dict, dict]):
    """Data Access Object for ContentReport operations."""

    def __init__(self, db: Session):
        super().__init__(ContentReport, db)

    def get_pending_reports(self, skip: int = 0, limit: int = 100) -> List[ContentReport]:
        """Get all pending content reports."""
        stmt = (
            select(ContentReport)
            .where(ContentReport.status == "pending")
            .order_by(ContentReport.submitted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_by_deck(self, deck_id: UUID) -> List[ContentReport]:
        """Get all reports for a specific deck."""
        stmt = (
            select(ContentReport)
            .where(ContentReport.deck_id == deck_id)
            .order_by(ContentReport.submitted_at.desc())
        )
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def mark_as_reviewed(
        self,
        report_id: UUID,
        reviewed_by: UUID,
        status: str,
        notes: Optional[str] = None
    ) -> Optional[ContentReport]:
        """Mark a report as reviewed."""
        report = self.get_by_id(report_id)
        if report:
            report.status = status
            report.reviewed_at = utcnow()
            report.reviewed_by = reviewed_by
            if notes:
                report.moderator_notes = notes
            self.db.commit()
            self.db.refresh(report)
        return report

