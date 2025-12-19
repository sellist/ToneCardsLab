"""Deck sharing and collaboration router."""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tcl_api.models import ApiResponse
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
from tcl_api.models.builders import ApiResponseBuilder
router = APIRouter(prefix="/sharing", tags=["sharing"])


@router.get("/decks/{deck_id}/viewers", response_model=ApiResponse[ViewersResponse])
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

    viewers_data = ViewersResponse(
        deck_id=str(deck_id),
        viewer_ids=[str(vid) for vid in viewer_ids]
    )

    return ApiResponseBuilder.ok().data(viewers_data.model_dump()).build()


@router.post("/decks/{deck_id}/viewers", response_model=ApiResponse[ViewersResponse])
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

    viewers_data = ViewersResponse(
        deck_id=str(deck_id),
        viewer_ids=[str(vid) for vid in viewer_ids]
    )

    return ApiResponseBuilder.ok().data(viewers_data.model_dump()).message("Viewers updated successfully").build()


@router.post("/decks/{deck_id}/share-by-email", response_model=ApiResponse[ShareByEmailResponse])
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
        "expires_at": datetime.now(datetime.timezone.utc) + timedelta(days=7)
    }

    invitation = invitation_dao.create(invitation_data)

    # In production, send actual email here
    # email_service.send_invitation(invitation)

    invitation_response = ShareByEmailResponse(
        invitation_id=str(invitation.invitation_id),
        status="sent",
        expires_at=invitation.expires_at.isoformat()
    )

    return ApiResponseBuilder.created().data(invitation_response.model_dump()).message("Invitation sent successfully").build()


@router.get("/invitations/{invitation_id}", response_model=ApiResponse[ShareByEmailResponse])
def get_invitation(invitation_id: UUID, db: Session = Depends(get_db)):
    """Get invitation details."""
    invitation_dao = DeckInvitationDAO(db)

    invitation = invitation_dao.get_by_id(invitation_id)
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    invitation_response = ShareByEmailResponse(
        invitation_id=str(invitation.invitation_id),
        status=invitation.status,
        expires_at=invitation.expires_at.isoformat() if invitation.expires_at else None
    )

    return ApiResponseBuilder.ok().data(invitation_response.model_dump()).build()


@router.post("/invitations/{invitation_id}/accept", response_model=ApiResponse)
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
    if invitation.expires_at < datetime.now(datetime.timezone.utc):
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

    return ApiResponseBuilder.ok().message("Invitation accepted successfully").build()


@router.get("/invitations/email/{email}", response_model=ApiResponse[List[ShareByEmailResponse]])
def get_user_invitations(email: str, db: Session = Depends(get_db)):
    """Get pending invitations for a user's email."""
    invitation_dao = DeckInvitationDAO(db)

    invitations = invitation_dao.get_pending_invitations(email)

    invitations_data = [
        ShareByEmailResponse(
            invitation_id=str(inv.invitation_id),
            status=inv.status,
            expires_at=inv.expires_at.isoformat() if inv.expires_at else None
        ).model_dump()
        for inv in invitations
    ]

    return ApiResponseBuilder.ok().data(invitations_data).build()


@router.delete("/invitations/{invitation_id}", response_model=ApiResponse)
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

    return ApiResponseBuilder.ok().message("Invitation revoked successfully").build()


@router.post("/decks/{deck_id}/viewers/{viewer_id}/remove", response_model=ApiResponse)
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

    return ApiResponseBuilder.ok().message("Viewer removed successfully").build()

