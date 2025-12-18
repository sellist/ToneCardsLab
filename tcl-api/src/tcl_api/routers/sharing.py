"""Deck sharing and collaboration router."""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import (
    DeckDAO, UserDAO, DeckViewerDAO, DeckInvitationDAO
)
from tcl_api.models.sharing import (
    ViewersResponse,
    EditViewersRequest,
    ShareByEmailRequest,
    ShareByEmailResponse
)
from tcl_api.models.common import SuccessResponse

router = APIRouter(prefix="/sharing", tags=["sharing"])


@router.get("/decks/{deck_id}/viewers", response_model=ViewersResponse)
def get_deck_viewers(deck_id: UUID, db: Session = Depends(get_db)):
    """Get list of users who have viewer access to a deck."""
    deck_dao = DeckDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    return ViewersResponse(
        deck_id=str(deck_id),
        viewer_ids=[str(vid) for vid in viewer_ids]
    )


@router.post("/decks/{deck_id}/viewers", response_model=ViewersResponse)
def edit_deck_viewers(
    deck_id: UUID,
    request: EditViewersRequest,
    owner_id: UUID = None,  # Should come from auth in production
    db: Session = Depends(get_db)
):
    """Add or remove viewers from a deck."""
    deck_dao = DeckDAO(db)
    user_dao = UserDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Verify ownership (in production, check against authenticated user)
    if owner_id and deck.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only deck owner can modify viewers"
        )

    # Add viewers
    for viewer_id in request.add_viewer_ids:
        # Check if user exists
        viewer = user_dao.get_by_id(UUID(viewer_id))
        if not viewer or viewer.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {viewer_id} not found"
            )

        # Add viewer if not already added
        if not viewer_dao.is_viewer(deck_id, UUID(viewer_id)):
            viewer_dao.add_viewer(
                deck_id=deck_id,
                viewer_id=UUID(viewer_id),
                granted_by=owner_id
            )

    # Remove viewers
    for viewer_id in request.remove_viewer_ids:
        viewer_dao.remove_viewer(deck_id, UUID(viewer_id))

    # Get updated viewer list
    viewer_ids = viewer_dao.get_viewer_ids(deck_id)

    return ViewersResponse(
        deck_id=str(deck_id),
        viewer_ids=[str(vid) for vid in viewer_ids]
    )


@router.post("/decks/{deck_id}/share-by-email", response_model=ShareByEmailResponse, status_code=status.HTTP_201_CREATED)
def share_deck_by_email(
    deck_id: UUID,
    request: ShareByEmailRequest,
    sender_id: UUID = None,  # Should come from auth in production
    db: Session = Depends(get_db)
):
    """Send an email invitation to share a deck."""
    deck_dao = DeckDAO(db)
    invitation_dao = DeckInvitationDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Verify ownership (in production, check against authenticated user)
    if sender_id and deck.owner_id != sender_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only deck owner can share deck"
        )

    # Create invitation
    invitation_data = {
        "deck_id": deck_id,
        "sender_id": sender_id or deck.owner_id,
        "recipient_email": request.recipient_email,
        "message": request.message,
        "status": "sent",
        "expires_at": datetime.utcnow() + timedelta(days=7)
    }

    invitation = invitation_dao.create(invitation_data)

    # In production, send actual email here
    # email_service.send_invitation(invitation)

    return ShareByEmailResponse(
        invitation_id=str(invitation.invitation_id),
        status="sent",
        expires_at=invitation.expires_at.isoformat()
    )


@router.get("/invitations/{invitation_id}", response_model=ShareByEmailResponse)
def get_invitation(invitation_id: UUID, db: Session = Depends(get_db)):
    """Get invitation details."""
    invitation_dao = DeckInvitationDAO(db)

    invitation = invitation_dao.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    return ShareByEmailResponse(
        invitation_id=str(invitation.invitation_id),
        status=invitation.status,
        expires_at=invitation.expires_at.isoformat() if invitation.expires_at else None
    )


@router.post("/invitations/{invitation_id}/accept", response_model=SuccessResponse)
def accept_invitation(
    invitation_id: UUID,
    user_email: str,  # Should come from authenticated user
    db: Session = Depends(get_db)
):
    """Accept a deck sharing invitation."""
    invitation_dao = DeckInvitationDAO(db)
    user_dao = UserDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Get invitation
    invitation = invitation_dao.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Verify recipient email matches
    if invitation.recipient_email != user_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation not for this user"
        )

    # Check if already accepted
    if invitation.status != "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation already {invitation.status}"
        )

    # Check expiration
    if invitation.expires_at < datetime.utcnow():
        invitation_dao.update(invitation_id, {"status": "expired"})
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired"
        )

    # Get user
    user = user_dao.get_by_email(user_email)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Add as viewer
    if not viewer_dao.is_viewer(invitation.deck_id, user.user_id):
        viewer_dao.add_viewer(
            deck_id=invitation.deck_id,
            viewer_id=user.user_id,
            granted_by=invitation.sender_id
        )

    # Mark invitation as accepted
    invitation_dao.accept_invitation(invitation_id)

    return SuccessResponse(
        success=True,
        message="Invitation accepted successfully"
    )


@router.get("/invitations/email/{email}", response_model=List[ShareByEmailResponse])
def get_user_invitations(email: str, db: Session = Depends(get_db)):
    """Get pending invitations for a user's email."""
    invitation_dao = DeckInvitationDAO(db)

    invitations = invitation_dao.get_pending_invitations(email)

    return [
        ShareByEmailResponse(
            invitation_id=str(inv.invitation_id),
            status=inv.status,
            expires_at=inv.expires_at.isoformat() if inv.expires_at else None
        )
        for inv in invitations
    ]


@router.delete("/invitations/{invitation_id}", response_model=SuccessResponse)
def revoke_invitation(
    invitation_id: UUID,
    db: Session = Depends(get_db)
):
    """Revoke a pending invitation."""
    invitation_dao = DeckInvitationDAO(db)

    invitation = invitation_dao.update(invitation_id, {"status": "revoked"})
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    return SuccessResponse(
        success=True,
        message="Invitation revoked successfully"
    )


@router.post("/decks/{deck_id}/viewers/{viewer_id}/remove", response_model=SuccessResponse)
def remove_viewer(
    deck_id: UUID,
    viewer_id: UUID,
    owner_id: UUID = None,  # Should come from auth
    db: Session = Depends(get_db)
):
    """Remove a viewer from a deck."""
    deck_dao = DeckDAO(db)
    viewer_dao = DeckViewerDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    # Verify ownership
    if owner_id and deck.owner_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only deck owner can remove viewers"
        )

    success = viewer_dao.remove_viewer(deck_id, viewer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Viewer not found for this deck"
        )

    return SuccessResponse(
        success=True,
        message="Viewer removed successfully"
    )

