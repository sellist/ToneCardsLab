"""Deck sharing and collaboration service."""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from tcl_api.config import get_logger
from tcl_api.internal.injectors import get_dao, initialize_dao_factory
from tcl_api.repository.db.models import Deck, DeckViewer, DeckInvitation


@get_dao(Deck)
@get_dao(DeckViewer)
@get_dao(DeckInvitation)
class SharingService:
    deck_dao: 'DeckDAO'
    viewer_dao: 'DeckViewerDAO'
    invitation_dao: 'DeckInvitationDAO'

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("services.sharing")
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

    def _check_ownership(self, deck: Deck, user_id: UUID) -> bool:
        if deck.owner_id != user_id:
            self.logger.warning(
                f"User {user_id} attempted to modify deck {deck.deck_id} they don't own"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only deck owner can perform this action"
            )
        return True

    def get_deck_viewers(self, deck_id: UUID) -> Dict[str, Any]:
        """Get list of users who have viewer access to a deck."""
        self.logger.debug(f"Retrieving viewers for deck {deck_id}")

        deck = self._check_deck_exists(deck_id)
        viewer_ids = self.viewer_dao.get_viewer_ids(deck_id)

        self.logger.info(f"Retrieved {len(viewer_ids)} viewers for deck {deck_id}")

        return {
            "deck_id": str(deck_id),
            "viewer_ids": [str(vid) for vid in viewer_ids]
        }

    def add_viewers(
        self,
        deck_id: UUID,
        viewer_ids: List[UUID],
        owner_id: UUID,
        user_dao: 'UserDAO'
    ) -> List[UUID]:
        """Add viewers to a deck."""
        self.logger.debug(f"Adding {len(viewer_ids)} viewers to deck {deck_id}")

        deck = self._check_deck_exists(deck_id)
        self._check_ownership(deck, owner_id)

        added_viewers = []

        for viewer_id in viewer_ids:
            user = user_dao.get_by_id(viewer_id)
            if not user or user.deleted_at:
                self.logger.warning(f"User {viewer_id} not found or deleted")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {viewer_id} not found"
                )

            if not self.viewer_dao.is_viewer(deck_id, viewer_id):
                self.viewer_dao.add_viewer(
                    deck_id=deck_id,
                    viewer_id=viewer_id,
                    granted_by=owner_id
                )
                added_viewers.append(viewer_id)
                self.logger.info(f"Added viewer {viewer_id} to deck {deck_id}")

        return added_viewers

    def remove_viewers(
        self,
        deck_id: UUID,
        viewer_ids: List[UUID],
        owner_id: UUID
    ) -> List[UUID]:
        """Remove viewers from a deck."""
        self.logger.debug(f"Removing {len(viewer_ids)} viewers from deck {deck_id}")

        deck = self._check_deck_exists(deck_id)
        self._check_ownership(deck, owner_id)

        removed_viewers = []

        for viewer_id in viewer_ids:
            success = self.viewer_dao.remove_viewer(deck_id, viewer_id)
            if success:
                removed_viewers.append(viewer_id)
                self.logger.info(f"Removed viewer {viewer_id} from deck {deck_id}")

        return removed_viewers

    def get_updated_viewers(self, deck_id: UUID) -> Dict[str, Any]:
        """Get current list of viewers for a deck."""
        viewer_ids = self.viewer_dao.get_viewer_ids(deck_id)
        return {
            "deck_id": str(deck_id),
            "viewer_ids": [str(vid) for vid in viewer_ids]
        }

    def create_invitation(
        self,
        deck_id: UUID,
        sender_id: UUID,
        recipient_email: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create and send a deck sharing invitation."""
        self.logger.debug(f"Creating invitation for {recipient_email} to deck {deck_id}")

        deck = self._check_deck_exists(deck_id)
        self._check_ownership(deck, sender_id)

        invitation_data = {
            "deck_id": deck_id,
            "sender_id": sender_id,
            "recipient_email": recipient_email,
            "message": message,
            "status": "sent",
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7)
        }

        invitation = self.invitation_dao.create(invitation_data)

        self.logger.info(f"Created invitation {invitation.invitation_id} for {recipient_email}")

        return {
            "invitation_id": str(invitation.invitation_id),
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat()
        }

    def get_invitation(self, invitation_id: UUID) -> Dict[str, Any]:
        """Get invitation details."""
        self.logger.debug(f"Retrieving invitation {invitation_id}")

        invitation = self.invitation_dao.get_by_id(invitation_id)
        if not invitation:
            self.logger.warning(f"Invitation not found: {invitation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        return {
            "invitation_id": str(invitation.invitation_id),
            "status": invitation.status,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None
        }

    def accept_invitation(
        self,
        invitation_id: UUID,
        user_email: str,
        user_id: UUID,
        user_dao: 'UserDAO'
    ) -> bool:
        """Accept a deck sharing invitation."""
        self.logger.debug(f"Accepting invitation {invitation_id} for user {user_id}")

        invitation = self.invitation_dao.get_by_id(invitation_id)
        if not invitation:
            self.logger.warning(f"Invitation not found: {invitation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        if invitation.recipient_email != user_email:
            self.logger.warning(
                f"Email mismatch for invitation {invitation_id}: {user_email} vs {invitation.recipient_email}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation not for this user"
            )

        if invitation.status != "sent":
            self.logger.warning(f"Invitation {invitation_id} already {invitation.status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}"
            )

        if invitation.expires_at < datetime.now(timezone.utc):
            self.invitation_dao.update(invitation_id, {"status": "expired"})
            self.logger.warning(f"Invitation {invitation_id} has expired")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Invitation has expired"
            )

        user = user_dao.get_by_id(user_id)
        if not user or user.deleted_at:
            self.logger.warning(f"User not found or deleted: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not self.viewer_dao.is_viewer(invitation.deck_id, user_id):
            self.viewer_dao.add_viewer(
                deck_id=invitation.deck_id,
                viewer_id=user_id,
                granted_by=invitation.sender_id
            )
            self.logger.info(f"Added user {user_id} as viewer to deck {invitation.deck_id}")

        self.invitation_dao.accept_invitation(invitation_id)

        self.logger.info(f"Invitation {invitation_id} accepted by user {user_id}")

        return True

    def get_pending_invitations(self, email: str) -> List[Dict[str, Any]]:
        """Get pending invitations for a user's email."""
        self.logger.debug(f"Retrieving pending invitations for {email}")

        invitations = self.invitation_dao.get_pending_invitations(email)

        invitations_data = [
            {
                "invitation_id": str(inv.invitation_id),
                "status": inv.status,
                "expires_at": inv.expires_at.isoformat() if inv.expires_at else None
            }
            for inv in invitations
        ]

        self.logger.info(f"Retrieved {len(invitations_data)} pending invitations for {email}")

        return invitations_data

    def revoke_invitation(self, invitation_id: UUID) -> bool:
        """Revoke a pending invitation."""
        self.logger.debug(f"Revoking invitation {invitation_id}")

        invitation = self.invitation_dao.update(invitation_id, {"status": "revoked"})
        if not invitation:
            self.logger.warning(f"Invitation not found: {invitation_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        self.logger.info(f"Invitation {invitation_id} revoked")

        return True

    def remove_viewer(
        self,
        deck_id: UUID,
        viewer_id: UUID,
        owner_id: UUID
    ) -> bool:
        """Remove a specific viewer from a deck."""
        self.logger.debug(f"Removing viewer {viewer_id} from deck {deck_id}")

        deck = self._check_deck_exists(deck_id)
        self._check_ownership(deck, owner_id)

        success = self.viewer_dao.remove_viewer(deck_id, viewer_id)
        if not success:
            self.logger.warning(f"Viewer {viewer_id} not found for deck {deck_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Viewer not found for this deck"
            )

        self.logger.info(f"Removed viewer {viewer_id} from deck {deck_id}")

        return True

