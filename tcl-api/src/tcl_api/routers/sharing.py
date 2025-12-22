"""Deck sharing and collaboration router."""

from typing import List
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from tcl_api.models.dto import ViewersResponse, ShareByEmailResponse, EditViewersRequest, ShareByEmailRequest
from tcl_api.models.response import ApiResponse
from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import UserDAO
from tcl_api.services.sharing import SharingService
from tcl_api.services.deck import DeckService

from tcl_api.models.builders import ApiResponseBuilder
router = APIRouter(prefix="/sharing", tags=["sharing"])


@router.get("/decks/{deck_id}/viewers", response_model=ApiResponse[ViewersResponse])
def get_deck_viewers(deck_id: UUID, db: Session = Depends(get_db)):
    """Get list of users who have viewer access to a deck."""
    sharing_service = SharingService(db)

    viewers_data = sharing_service.get_deck_viewers(deck_id)

    return ApiResponseBuilder.ok().data(viewers_data).build()


@router.post("/decks/{deck_id}/viewers", response_model=ApiResponse[ViewersResponse])
def edit_deck_viewers(
    deck_id: UUID,
    request: EditViewersRequest,
    owner_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Add or remove viewers from a deck."""
    sharing_service = SharingService(db)
    user_dao = UserDAO(db)

    if request.add_viewer_ids:
        sharing_service.add_viewers(deck_id, request.add_viewer_ids, owner_id, user_dao)

    if request.remove_viewer_ids:
        sharing_service.remove_viewers(deck_id, request.remove_viewer_ids, owner_id)

    viewers_data = sharing_service.get_updated_viewers(deck_id)

    return ApiResponseBuilder.ok().data(viewers_data).message("Viewers updated successfully").build()


@router.post("/decks/{deck_id}/share-by-email", response_model=ApiResponse[ShareByEmailResponse])
def share_deck_by_email(
    deck_id: UUID,
    request: ShareByEmailRequest,
    sender_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Send an email invitation to share a deck."""
    sharing_service = SharingService(db)

    invitation_data = sharing_service.create_invitation(
        deck_id=deck_id,
        sender_id=sender_id,
        recipient_email=request.recipient_email,
        message=request.message
    )

    return ApiResponseBuilder.created().data(invitation_data).message("Invitation sent successfully").build()


@router.get("/invitations/{invitation_id}", response_model=ApiResponse[ShareByEmailResponse])
def get_invitation(invitation_id: UUID, db: Session = Depends(get_db)):
    """Get invitation details."""
    sharing_service = SharingService(db)

    invitation_data = sharing_service.get_invitation(invitation_id)

    return ApiResponseBuilder.ok().data(invitation_data).build()


@router.post("/invitations/{invitation_id}/accept", response_model=ApiResponse)
def accept_invitation(
    invitation_id: UUID,
    user_email: str,
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """Accept a deck sharing invitation."""
    sharing_service = SharingService(db)
    user_dao = UserDAO(db)

    sharing_service.accept_invitation(invitation_id, user_email, user_id, user_dao)

    return ApiResponseBuilder.ok().message("Invitation accepted successfully").build()


@router.get("/invitations/email/{email}", response_model=ApiResponse[List[ShareByEmailResponse]])
def get_user_invitations(email: str, db: Session = Depends(get_db)):
    """Get pending invitations for a user's email."""
    sharing_service = SharingService(db)

    invitations_data = sharing_service.get_pending_invitations(email)

    return ApiResponseBuilder.ok().data(invitations_data).build()


@router.delete("/invitations/{invitation_id}", response_model=ApiResponse)
def revoke_invitation(
    invitation_id: UUID,
    db: Session = Depends(get_db)
):
    """Revoke a pending invitation."""
    sharing_service = SharingService(db)

    sharing_service.revoke_invitation(invitation_id)

    return ApiResponseBuilder.ok().message("Invitation revoked successfully").build()


@router.post("/decks/{deck_id}/viewers/{viewer_id}/remove", response_model=ApiResponse)
def remove_viewer(
    deck_id: UUID,
    viewer_id: UUID,
    owner_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Remove a viewer from a deck."""
    sharing_service = SharingService(db)

    sharing_service.remove_viewer(deck_id, viewer_id, owner_id)

    return ApiResponseBuilder.ok().message("Viewer removed successfully").build()

