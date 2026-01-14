"""File management service."""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from tcl_api.config import get_logger
from tcl_api.internal.injectors import get_dao, initialize_dao_factory
from tcl_api.models.db.entities import UploadedFile
from tcl_api.models.file import FileRead
from tcl_api.models.mappers import file_to_read


@get_dao(UploadedFile)
class FileService:
    file_dao: 'UploadedFileDAO'

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("services.file")
        initialize_dao_factory(db)

    def _check_file_exists(self, file_id: UUID) -> UploadedFile:
        file = self.file_dao.get_by_id(file_id)
        if not file or file.deleted_at:
            self.logger.warning(f"File not found or deleted: {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        return file

    def get_file(self, file_id: UUID) -> FileRead:
        """Get file metadata by ID."""
        self.logger.debug(f"Retrieving file {file_id}")

        file = self._check_file_exists(file_id)

        self.logger.info(f"Successfully retrieved file {file_id}")
        return file_to_read(file)

    def get_user_files(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[FileRead], int]:
        """Get all files uploaded by a user."""
        self.logger.debug(f"Retrieving files for user {user_id}")

        files = self.file_dao.get_by_user(user_id, skip=skip, limit=limit)
        total_size = self.file_dao.get_total_size_by_user(user_id)

        self.logger.info(f"Retrieved {len(files)} files for user {user_id}")

        return [file_to_read(f) for f in files], total_size

    def get_deck_files(self, deck_id: UUID) -> List[FileRead]:
        """Get all files associated with a deck."""
        self.logger.debug(f"Retrieving files for deck {deck_id}")

        files = self.file_dao.get_by_deck(deck_id)

        self.logger.info(f"Retrieved {len(files)} files for deck {deck_id}")

        return [file_to_read(f) for f in files]

    def create_file(
        self,
        user_id: UUID,
        file_name: str,
        file_size: int,
        mime_type: str,
        file_url: str,
        deck_id: Optional[UUID] = None
    ) -> FileRead:
        """Create a new file record."""
        self.logger.debug(f"Creating file {file_name} for user {user_id}")

        file_data = {
            "user_id": user_id,
            "deck_id": deck_id,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "file_url": file_url
        }

        file = self.file_dao.create(file_data)

        self.logger.info(f"Successfully created file {file.file_id}")
        return file_to_read(file)

    def delete_file(self, file_id: UUID) -> bool:
        """Soft delete a file."""
        self.logger.debug(f"Deleting file {file_id}")

        file = self.file_dao.soft_delete(file_id)

        if not file:
            self.logger.warning(f"Failed to delete file {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        self.logger.info(f"Successfully deleted file {file_id}")
        return True

    def permanently_delete_file(self, file_id: UUID) -> bool:
        self.logger.debug(f"Permanently deleting file {file_id}")

        file = self.file_dao.get_by_id(file_id)
        if not file:
            self.logger.warning(f"File not found: {file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        success = self.file_dao.delete(file_id)

        if not success:
            self.logger.error(f"Failed to permanently delete file {file_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )

        self.logger.info(f"Successfully permanently deleted file {file_id}")
        return True

