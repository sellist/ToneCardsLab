"""
Example usage of the DAO pattern in ToneCards Lab.

This file demonstrates how to use the BaseDAO and concrete DAOs
for database operations in the application.
"""

from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from tcl_api.repository.db import get_db, get_db_context
from tcl_api.repository.db.daos import (
    UserDAO, DeckDAO, CardDAO, DeckViewerDAO,
    DeckInvitationDAO, UploadedFileDAO, ContentReportDAO
)
from tcl_api.repository.db.models import User, Deck, Card, RendererType


# Example 1: Using DAOs with FastAPI dependency injection
# -------------------------------------------------------
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get a user by ID using UserDAO."""
    user_dao = UserDAO(db)
    user = user_dao.get_by_id(user_id)
    return user


@router.get("/users/email/{email}")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """Get a user by email using custom DAO method."""
    user_dao = UserDAO(db)
    user = user_dao.get_by_email(email)
    return user


@router.post("/users")
def create_user(email: str, name: str, db: Session = Depends(get_db)):
    """Create a new user."""
    user_dao = UserDAO(db)
    user_data = {
        "email": email,
        "name": name,
        "preferences": {}
    }
    user = user_dao.create(user_data)
    return user


# Example 2: Using DAOs with context manager
# ------------------------------------------
def create_deck_with_cards(owner_id: UUID, title: str, cards_data: list):
    """Create a deck with cards using context manager."""
    with get_db_context() as db:
        # Create deck
        deck_dao = DeckDAO(db)
        deck_data = {
            "owner_id": owner_id,
            "title": title,
            "description": "My new deck",
            "is_public": False
        }
        deck = deck_dao.create(deck_data)

        # Create cards for the deck
        card_dao = CardDAO(db)
        for i, card_data in enumerate(cards_data):
            card = card_dao.create({
                "deck_id": deck.deck_id,
                "front_content": card_data["front"],
                "back_content": card_data["back"],
                "front_renderer": RendererType.MARKDOWN,
                "back_renderer": RendererType.MARKDOWN,
                "position": i
            })

        return deck


# Example 3: Complex queries using custom DAO methods
# ---------------------------------------------------
def get_user_dashboard_data(user_id: UUID, db: Session):
    """Get comprehensive dashboard data for a user."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)

    # Get user info
    user = user_dao.get_by_id(user_id)
    if not user:
        return None

    # Get owned decks
    owned_decks = deck_dao.get_by_owner(user_id, skip=0, limit=10)

    # Get shared decks
    shared_decks = deck_dao.get_shared_with_user(user_id, skip=0, limit=10)

    return {
        "user": user,
        "owned_decks": owned_decks,
        "shared_decks": shared_decks,
        "total_owned": deck_dao.count_by_owner(user_id)
    }


# Example 4: Sharing and permissions
# -----------------------------------
def share_deck_with_user(
    deck_id: UUID,
    owner_id: UUID,
    viewer_email: str,
    db: Session
):
    """Share a deck with another user."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Verify deck ownership
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.owner_id != owner_id:
        raise ValueError("Deck not found or not owned by user")

    # Find viewer by email
    viewer = user_dao.get_by_email(viewer_email)
    if not viewer:
        raise ValueError("Viewer not found")

    # Add viewer
    viewer_dao.add_viewer(
        deck_id=deck_id,
        viewer_id=viewer.user_id,
        granted_by=owner_id
    )

    return {"success": True, "viewer_id": viewer.user_id}


# Example 5: Invitation workflow
# -------------------------------
def create_deck_invitation(
    deck_id: UUID,
    sender_id: UUID,
    recipient_email: str,
    message: str,
    db: Session
):
    """Create an invitation to share a deck."""
    invitation_dao = DeckInvitationDAO(db)

    invitation_data = {
        "deck_id": deck_id,
        "sender_id": sender_id,
        "recipient_email": recipient_email,
        "message": message,
        "status": "sent",
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }

    invitation = invitation_dao.create(invitation_data)
    return invitation


def accept_deck_invitation(invitation_id: UUID, user_email: str, db: Session):
    """Accept a deck invitation."""
    invitation_dao = DeckInvitationDAO(db)
    viewer_dao = DeckViewerDAO(db)
    user_dao = UserDAO(db)

    # Get invitation
    invitation = invitation_dao.get_by_id(invitation_id)
    if not invitation or invitation.recipient_email != user_email:
        raise ValueError("Invalid invitation")

    if invitation.status != "sent":
        raise ValueError("Invitation already processed")

    if invitation.expires_at < datetime.utcnow():
        raise ValueError("Invitation expired")

    # Get user
    user = user_dao.get_by_email(user_email)
    if not user:
        raise ValueError("User not found")

    # Add as viewer
    viewer_dao.add_viewer(
        deck_id=invitation.deck_id,
        viewer_id=user.user_id,
        granted_by=invitation.sender_id
    )

    # Mark invitation as accepted
    invitation_dao.accept_invitation(invitation_id)

    return {"success": True}


# Example 6: File management
# ---------------------------
def upload_file_to_deck(
    user_id: UUID,
    deck_id: UUID,
    file_name: str,
    file_size: int,
    mime_type: str,
    file_url: str,
    db: Session
):
    """Upload a file and associate it with a deck."""
    file_dao = UploadedFileDAO(db)

    file_data = {
        "user_id": user_id,
        "deck_id": deck_id,
        "file_name": file_name,
        "file_size": file_size,
        "mime_type": mime_type,
        "file_url": file_url
    }

    file = file_dao.create(file_data)
    return file


# Example 7: Soft delete and recovery
# ------------------------------------
def soft_delete_deck(deck_id: UUID, db: Session):
    """Soft delete a deck."""
    deck_dao = DeckDAO(db)
    deck = deck_dao.soft_delete(deck_id)
    return deck


def restore_deck(deck_id: UUID, db: Session):
    """Restore a soft-deleted deck."""
    deck_dao = DeckDAO(db)
    deck = deck_dao.get_by_id(deck_id)
    if deck and deck.deleted_at:
        deck.deleted_at = None
        deck_dao.commit()
        return deck_dao.refresh(deck)
    return None


# Example 8: Bulk operations
# ---------------------------
def bulk_delete_decks(deck_ids: list[UUID], db: Session):
    """Delete multiple decks at once."""
    deck_dao = DeckDAO(db)
    deleted_count = deck_dao.bulk_delete(deck_ids)
    return {"deleted": deleted_count}


# Example 9: Search functionality
# --------------------------------
def search_public_decks(query: str, page: int = 1, page_size: int = 20, db: Session):
    """Search public decks by title or description."""
    deck_dao = DeckDAO(db)
    skip = (page - 1) * page_size
    decks = deck_dao.search_decks(
        query=query,
        is_public=True,
        skip=skip,
        limit=page_size
    )
    return decks


# Example 10: Content moderation
# -------------------------------
def submit_content_report(
    deck_id: UUID,
    reporter_id: UUID,
    reason: str,
    description: str,
    db: Session
):
    """Submit a content report for a deck."""
    report_dao = ContentReportDAO(db)

    report_data = {
        "deck_id": deck_id,
        "reporter_id": reporter_id,
        "reason": reason,
        "description": description,
        "status": "pending"
    }

    report = report_dao.create(report_data)
    return report


def review_content_report(
    report_id: UUID,
    moderator_id: UUID,
    action: str,
    notes: str,
    db: Session
):
    """Review and action a content report."""
    report_dao = ContentReportDAO(db)

    report = report_dao.mark_as_reviewed(
        report_id=report_id,
        reviewed_by=moderator_id,
        status=action,
        notes=notes
    )

    return report


# Example 11: Transaction management
# -----------------------------------
def transfer_deck_ownership(
    deck_id: UUID,
    current_owner_id: UUID,
    new_owner_id: UUID,
    db: Session
):
    """Transfer deck ownership with transaction."""
    try:
        deck_dao = DeckDAO(db)
        viewer_dao = DeckViewerDAO(db)

        # Get deck
        deck = deck_dao.get_by_id(deck_id)
        if not deck or deck.owner_id != current_owner_id:
            raise ValueError("Deck not found or not owned by user")

        # Remove new owner from viewers if present
        viewer_dao.remove_viewer(deck_id, new_owner_id)

        # Update owner
        deck.owner_id = new_owner_id
        deck_dao.commit()

        return deck_dao.refresh(deck)
    except Exception as e:
        deck_dao.rollback()
        raise

