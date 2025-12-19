"""File upload and management router."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from tcl_api.repository.db import get_db
from tcl_api.repository.db.daos import UploadedFileDAO, UserDAO, DeckDAO
from tcl_api.models.file import (
    UploadedFile as UploadedFileModel,
    UserFilesResponse
)
from tcl_api.models.builders import ApiResponseBuilder
from tcl_api.models.response import ApiResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=ApiResponse[UploadedFileModel])
async def upload_file(
    file: UploadFile = File(...),
    user_id: UUID = Query(..., description="User ID uploading the file"),
    deck_id: UUID = Query(None, description="Optional deck ID to associate"),
    db: Session = Depends(get_db)
):
    """Upload a file and store metadata."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)
    file_dao = UploadedFileDAO(db)

    # Verify user exists
    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify deck if provided
    if deck_id:
        deck = deck_dao.get_by_id(deck_id)
        if not deck or deck.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # In production, upload to S3/storage service
    # For now, create a mock URL
    file_url = f"https://storage.example.com/files/{file.filename}"

    # Store file metadata
    file_data = {
        "user_id": user_id,
        "deck_id": deck_id,
        "file_name": file.filename,
        "file_size": file_size,
        "mime_type": file.content_type or "application/octet-stream",
        "file_url": file_url
    }

    uploaded_file = file_dao.create(file_data)

    file_response = UploadedFileModel(
        file_id=str(uploaded_file.file_id),
        file_url=uploaded_file.file_url,
        file_name=uploaded_file.file_name,
        file_size=uploaded_file.file_size,
        mime_type=uploaded_file.mime_type,
        uploaded_at=uploaded_file.uploaded_at,
        deck_id=str(uploaded_file.deck_id) if uploaded_file.deck_id else None
    )

    return ApiResponseBuilder.created().data(file_response.model_dump()).message("File uploaded successfully").build()


@router.get("/{file_id}", response_model=ApiResponse[UploadedFileModel])
def get_file(file_id: UUID, db: Session = Depends(get_db)):
    """Get file metadata by ID."""
    file_dao = UploadedFileDAO(db)

    file = file_dao.get_by_id(file_id)
    if not file or file.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    file_response = UploadedFileModel(
        file_id=str(file.file_id),
        file_url=file.file_url,
        file_name=file.file_name,
        file_size=file.file_size,
        mime_type=file.mime_type,
        uploaded_at=file.uploaded_at,
        deck_id=str(file.deck_id) if file.deck_id else None
    )

    return ApiResponseBuilder.ok().data(file_response.model_dump()).build()


@router.get("/user/{user_id}", response_model=ApiResponse[UserFilesResponse])
def get_user_files(
    user_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all files uploaded by a user."""
    user_dao = UserDAO(db)
    file_dao = UploadedFileDAO(db)

    # Verify user exists
    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    files = file_dao.get_by_user(user_id, skip=skip, limit=limit)
    total_size = file_dao.get_total_size_by_user(user_id)

    file_models = [
        UploadedFileModel(
            file_id=str(f.file_id),
            file_url=f.file_url,
            file_name=f.file_name,
            file_size=f.file_size,
            mime_type=f.mime_type,
            uploaded_at=f.uploaded_at,
            deck_id=str(f.deck_id) if f.deck_id else None
        )
        for f in files
    ]

    user_files_response = UserFilesResponse(
        files=file_models,
        total_size=total_size,
        total_count=len(files)
    )

    return ApiResponseBuilder.ok().data(user_files_response.model_dump()).build()


@router.get("/deck/{deck_id}", response_model=ApiResponse[List[UploadedFileModel]])
def get_deck_files(deck_id: UUID, db: Session = Depends(get_db)):
    """Get all files associated with a deck."""
    deck_dao = DeckDAO(db)
    file_dao = UploadedFileDAO(db)

    # Verify deck exists
    deck = deck_dao.get_by_id(deck_id)
    if not deck or deck.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

    files = file_dao.get_by_deck(deck_id)

    file_models = [
        UploadedFileModel(
            file_id=str(f.file_id),
            file_url=f.file_url,
            file_name=f.file_name,
            file_size=f.file_size,
            mime_type=f.mime_type,
            uploaded_at=f.uploaded_at,
            deck_id=str(f.deck_id) if f.deck_id else None
        ).model_dump()
        for f in files
    ]

    return ApiResponseBuilder.ok().data(file_models).build()


@router.delete("/{file_id}", response_model=ApiResponse)
def delete_file(file_id: UUID, db: Session = Depends(get_db)):
    """Delete a file (soft delete)."""
    file_dao = UploadedFileDAO(db)

    file = file_dao.soft_delete(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # In production, also delete from storage service
    # storage_service.delete(file.file_url)

    return ApiResponseBuilder.ok().message("File deleted successfully").build()


@router.delete("/{file_id}/permanent", response_model=ApiResponse)
def permanently_delete_file(
    file_id: UUID,
    db: Session = Depends(get_db)
):
    """Permanently delete a file from database and storage."""
    file_dao = UploadedFileDAO(db)

    # Get file first to access URL
    file = file_dao.get_by_id(file_id)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Delete from storage (in production)
    # storage_service.delete(file.file_url)

    # Hard delete from database
    success = file_dao.delete(file_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )

    return ApiResponseBuilder.ok().message("File permanently deleted").build()


@router.post("/bulk-upload", response_model=ApiResponse[List[UploadedFileModel]])
async def bulk_upload_files(
    files: List[UploadFile] = File(...),
    user_id: UUID = Query(..., description="User ID uploading files"),
    deck_id: UUID = Query(None, description="Optional deck ID to associate"),
    db: Session = Depends(get_db)
):
    """Upload multiple files at once."""
    user_dao = UserDAO(db)
    deck_dao = DeckDAO(db)
    file_dao = UploadedFileDAO(db)

    # Verify user exists
    user = user_dao.get_by_id(user_id)
    if not user or user.deleted_at:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Verify deck if provided
    if deck_id:
        deck = deck_dao.get_by_id(deck_id)
        if not deck or deck.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found"
            )

    uploaded_files = []

    for file in files:
        content = await file.read()
        file_size = len(content)

        # Mock file URL (in production, upload to storage)
        file_url = f"https://storage.example.com/files/{file.filename}"

        file_data = {
            "user_id": user_id,
            "deck_id": deck_id,
            "file_name": file.filename,
            "file_size": file_size,
            "mime_type": file.content_type or "application/octet-stream",
            "file_url": file_url
        }

        uploaded_file = file_dao.create(file_data)
        uploaded_files.append(UploadedFileModel(
            file_id=str(uploaded_file.file_id),
            file_url=uploaded_file.file_url,
            file_name=uploaded_file.file_name,
            file_size=uploaded_file.file_size,
            mime_type=uploaded_file.mime_type,
            uploaded_at=uploaded_file.uploaded_at,
            deck_id=str(uploaded_file.deck_id) if uploaded_file.deck_id else None
        ).model_dump())

    return ApiResponseBuilder.created().data(uploaded_files).message(f"Successfully uploaded {len(uploaded_files)} files").build()

