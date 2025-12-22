from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.services.user import UserService
from tcl_api.models.user import User, UserCreate, UserUpdate, UserDeleteConfirm
from tcl_api.models.common import ApiResponse
from tcl_api.models.builders import ApiResponseBuilder

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=ApiResponse[User])
def create_user(
    create_data: UserCreate,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.create_user(email=create_data.email, name=create_data.name)
    return ApiResponseBuilder.created().data(user.serialize(0, 0)).build()


@router.get("/{user_id}", response_model=ApiResponse[User])
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user_data = user_service.get_user_by_id(user_id)
    return ApiResponseBuilder.ok().data(user_data).build()


@router.get("/email/{email}", response_model=ApiResponse[User])
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user_service = UserService(db)
    user_data = user_service.get_user_by_email(email)
    return ApiResponseBuilder.ok().data(user_data).build()


@router.patch("/{user_id}", response_model=ApiResponse[User])
def update_user(
    user_id: UUID,
    update_data: UserUpdate,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    updated_user_data = user_service.update_user(
        user_id=user_id,
        name=update_data.name
    )
    return ApiResponseBuilder.ok().data(updated_user_data).build()


@router.delete("/{user_id}", response_model=ApiResponse)
def delete_user(
    user_id: UUID,
    request: UserDeleteConfirm,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)

    user = user_service.user_dao.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if request.confirmation != user.email and request.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation"
        )

    user_service.delete_user(user_id)
    return ApiResponseBuilder.ok().message("User account deleted successfully").build()


@router.get("/", response_model=ApiResponse[List[User]])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    users = user_service.list_users(skip=skip, limit=limit, search=search)
    return ApiResponseBuilder.ok().data(users).build()

