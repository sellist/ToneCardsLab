"""File upload and management router."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import UploadedFileDAO, UserDAO, DeckDAO
from tcl_api.services.file import FileService
from tcl_api.services.deck import DeckService
from tcl_api.models.file import (
    UploadedFile as UploadedFileModel,
    UserFilesResponse
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.common import ApiResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=ApiResponse[UploadedFileModel])
async def upload_file(
    file: UploadFile = File(...),
    user_id: UUID = Query(..., description="User ID uploading the file"),
    deck_id: UUID = Query(None, description="Optional deck ID to associate"),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    user_dao = UserDAO(db)
    deck_service = DeckService(db)

    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if deck_id:
        deck_service._check_deck_exists(deck_id)

    content = await file.read()
    file_size = len(content)

    file_url = f"https://storage.example.com/files/{file.filename}"

    file_response_data = file_service.create_file(
        user_id=user_id,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_url=file_url,
        deck_id=deck_id
    )

    return ApiResponseBuilder.created().data(file_response_data).message("File uploaded successfully").build()


@router.get("/{file_id}", response_model=ApiResponse[UploadedFileModel])
def get_file(file_id: UUID, db: Session = Depends(get_db)):
    file_service = FileService(db)

    file_data = file_service.get_file(file_id)

    return ApiResponseBuilder.ok().data(file_data).build()


@router.get("/user/{user_id}", response_model=ApiResponse[UserFilesResponse])
def get_user_files(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    file_service = FileService(db)
    user_dao = UserDAO(db)

    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    files_data, total_size = file_service.get_user_files(user_id, skip=skip, limit=limit)

    user_files_response = UserFilesResponse(
        files=[UploadedFileModel(**f) for f in files_data],
        total_size=total_size,
        total_count=len(files_data)
    )

    return ApiResponseBuilder.ok().data(user_files_response.model_dump()).build()


@router.get("/deck/{deck_id}", response_model=ApiResponse[List[UploadedFileModel]])
def get_deck_files(deck_id: UUID, db: Session = Depends(get_db)):
    """Get all files associated with a deck."""
    file_service = FileService(db)

    files_data = file_service.get_deck_files(deck_id)

    file_models = [UploadedFileModel(**f) for f in files_data]

    return ApiResponseBuilder.ok().data([f.model_dump() for f in file_models]).build()


@router.delete("/{file_id}", response_model=ApiResponse)
def delete_file(file_id: UUID, db: Session = Depends(get_db)):
    """Delete a file (soft delete)."""
    file_service = FileService(db)

    file_service.delete_file(file_id)

    return ApiResponseBuilder.ok().message("File deleted successfully").build()


@router.delete("/{file_id}/permanent", response_model=ApiResponse)
def permanently_delete_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    file_service = FileService(db)

    file_service.permanently_delete_file(file_id)

    return ApiResponseBuilder.ok().message("File permanently deleted").build()


@router.post("/bulk-upload", response_model=ApiResponse[List[UploadedFileModel]])
async def bulk_upload_files(
    files: List[UploadFile] = File(...),
    user_id: UUID = Query(..., description="User ID uploading files"),
    deck_id: UUID = Query(None, description="Optional deck ID to associate"),
    db: Session = Depends(get_db)
):
    """Upload multiple files at once."""
    file_service = FileService(db)
    user_dao = UserDAO(db)
    deck_service = DeckService(db)

    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if deck_id:
        deck_service._check_deck_exists(deck_id)

    uploaded_files = []

    for file in files:
        content = await file.read()
        file_size = len(content)

        file_url = f"https://storage.example.com/files/{file.filename}"

        file_data = file_service.create_file(
            user_id=user_id,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type or "application/octet-stream",
            file_url=file_url,
            deck_id=deck_id
        )

        uploaded_files.append(file_data)

    return ApiResponseBuilder.created().data(uploaded_files).message(f"Successfully uploaded {len(uploaded_files)} files").build()

