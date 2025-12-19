"""User management router."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import UserDAO
from tcl_api.models.user import (
    UserProfileResponse,
    UpdateUserProfileRequest,
    DeleteAccountRequest
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.response import ApiResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=ApiResponse[UserProfileResponse])
def create_user(
    email: str,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new user account."""
    user_dao = UserDAO(db)

    # Check if user already exists
    existing_user = user_dao.get_by_email(email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    # Create user
    user_data = {
        "email": email,
        "name": name,
        "preferences": {}
    }
    user = user_dao.create(user_data)

    user_response = UserProfileResponse(
        user_id=str(user.user_id),
        email=user.email,
        name=user.name,
        preferences=user.preferences,
        created_at=user.created_at,
        updated_at=user.updated_at,
        owned_decks_count=0,
        shared_decks_count=0
    )

    return ApiResponseBuilder.created().data(user_response.model_dump()).message("User created successfully").build()


@router.get("/{user_id}", response_model=ApiResponse[UserProfileResponse])
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """Get user profile by ID."""
    user_dao = UserDAO(db)
    user = user_dao.get_by_id(user_id)

    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Count decks (simplified - would use proper DAO methods)
    from tcl_api.repository.db.daos import DeckDAO, DeckViewerDAO
    deck_dao = DeckDAO(db)
    viewer_dao = DeckViewerDAO(db)

    owned_count = deck_dao.count_by_owner(user.user_id)
    shared_decks = deck_dao.get_shared_with_user(user.user_id)

    user_response = UserProfileResponse(
        user_id=str(user.user_id),
        email=user.email,
        name=user.name,
        preferences=user.preferences,
        created_at=user.created_at,
        updated_at=user.updated_at,
        owned_decks_count=owned_count,
        shared_decks_count=len(shared_decks)
    )

    return ApiResponseBuilder.ok().data(user_response.model_dump()).build()


@router.get("/email/{email}", response_model=ApiResponse[UserProfileResponse])
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    """Get user profile by email address."""
    user_dao = UserDAO(db)
    user = user_dao.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    from tcl_api.repository.db.daos import DeckDAO
    deck_dao = DeckDAO(db)
    owned_count = deck_dao.count_by_owner(user.user_id)
    shared_decks = deck_dao.get_shared_with_user(user.user_id)

    user_response = UserProfileResponse(
        user_id=str(user.user_id),
        email=user.email,
        name=user.name,
        preferences=user.preferences,
        created_at=user.created_at,
        updated_at=user.updated_at,
        owned_decks_count=owned_count,
        shared_decks_count=len(shared_decks)
    )

    return ApiResponseBuilder.ok().data(user_response.model_dump()).build()


@router.patch("/{user_id}", response_model=ApiResponse[UserProfileResponse])
def update_user(
    user_id: UUID,
    update_data: UpdateUserProfileRequest,
    db: Session = Depends(get_db)
):
    """Update user profile."""
    user_dao = UserDAO(db)

    # Convert Pydantic model to dict
    update_dict = update_data.model_dump(exclude_unset=True)

    user = user_dao.update(user_id, update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    from tcl_api.repository.db.daos import DeckDAO
    deck_dao = DeckDAO(db)
    owned_count = deck_dao.count_by_owner(user.user_id)
    shared_decks = deck_dao.get_shared_with_user(user.user_id)

    user_response = UserProfileResponse(
        user_id=str(user.user_id),
        email=user.email,
        name=user.name,
        preferences=user.preferences,
        created_at=user.created_at,
        updated_at=user.updated_at,
        owned_decks_count=owned_count,
        shared_decks_count=len(shared_decks)
    )

    return ApiResponseBuilder.ok().data(user_response.model_dump()).message("User updated successfully").build()


@router.delete("/{user_id}", response_model=ApiResponse)
def delete_user(
    user_id: UUID,
    request: DeleteAccountRequest,
    db: Session = Depends(get_db)
):
    """Delete user account (soft delete)."""
    user_dao = UserDAO(db)

    # Verify user exists
    user = user_dao.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify confirmation (simple check - in production use proper auth)
    if request.confirmation != user.email and request.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation"
        )

    # Soft delete user
    user_dao.soft_delete(user_id)

    return ApiResponseBuilder.ok().message("User account deleted successfully").build()


@router.get("/", response_model=ApiResponse[List[UserProfileResponse]])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List users with optional search."""
    user_dao = UserDAO(db)

    if search:
        users = user_dao.search_by_name_or_email(search, skip=skip, limit=limit)
    else:
        users = user_dao.get_active_users(skip=skip, limit=limit)

    result = []
    for user in users:
        result.append(UserProfileResponse(
            user_id=str(user.user_id),
            email=user.email,
            name=user.name,
            preferences=user.preferences,
            created_at=user.created_at,
            updated_at=user.updated_at,
            owned_decks_count=0,
            shared_decks_count=0
        ).model_dump())

    return ApiResponseBuilder.ok().data(result).build()

