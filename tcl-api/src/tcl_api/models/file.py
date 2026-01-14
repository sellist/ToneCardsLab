from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class UploadFileRequest(BaseModel):
    deck_id: Optional[UUID] = Field(default=None, description="Optional associated deck ID")
    file_name: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type of the file")


class FileRead(BaseModel):
    file_id: UUID = Field(..., description="UUID of the file")
    file_url: str = Field(..., description="URL to access the file")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    deck_id: Optional[UUID] = Field(None, description="Associated deck ID if applicable")


class UserFilesResponse(BaseModel):
    files: List[FileRead] = Field(default_factory=list, description="List of uploaded files")
    total_size: int = Field(..., description="Total size of all files in bytes")
    total_count: int = Field(..., description="Total number of files")


class DeleteFileRequest(BaseModel):
    file_id: UUID = Field(..., description="UUID of file to delete")
