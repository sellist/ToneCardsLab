"""File upload and management Pydantic models."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

class UploadedFile(BaseModel):
    """Uploaded file metadata."""
    file_id: str = Field(..., description="UUID of the file")
    file_url: str = Field(..., description="URL to access the file")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    deck_id: Optional[str] = Field(None, description="Associated deck ID if applicable")


class UserFilesResponse(BaseModel):
    """Response with list of user's uploaded files."""
    files: List[UploadedFile] = Field(default_factory=list, description="List of uploaded files")
    total_size: int = Field(..., description="Total size of all files in bytes")
    total_count: int = Field(..., description="Total number of files")


class DeleteFileRequest(BaseModel):
    """Request to delete an uploaded file."""
    file_id: str = Field(..., description="UUID of file to delete")

