"""User management router."""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.services.user import UserService
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
    user_service = UserService(db)
    user = user_service.create_user(email=email, name=name)

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
    user_service = UserService(db)
    user_data = user_service.get_user_by_id(user_id)

    return ApiResponseBuilder.ok().data(user_data).build()


@router.get("/email/{email}", response_model=ApiResponse[UserProfileResponse])
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user_data = user_service.get_user_by_email(email)

    return ApiResponseBuilder.ok().data(user_data).build()


@router.patch("/{user_id}", response_model=ApiResponse[UserProfileResponse])
def update_user(
    user_id: UUID,
    update_data: UpdateUserProfileRequest,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    updated_user_data = user_service.update_user(
        user_id=user_id,
        name=update_data.name,
        preferences=update_data.preferences
    )

    return ApiResponseBuilder.ok().data(updated_user_data).message("User updated successfully").build()


@router.delete("/{user_id}", response_model=ApiResponse)
def delete_user(
    user_id: UUID,
    request: DeleteAccountRequest,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)

    user = user_service.user_dao.get_by_id(user_id)
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

    user_service.delete_user(user_id)

    return ApiResponseBuilder.ok().message("User account deleted successfully").build()


@router.get("/", response_model=ApiResponse[List[UserProfileResponse]])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    users = user_service.list_users(skip=skip, limit=limit, search=search)

    return ApiResponseBuilder.ok().data(users).build()
