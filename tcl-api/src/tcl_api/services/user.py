"""User service with business logic."""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from tcl_api.config import get_logger
from tcl_api.internal.injectors import get_dao, initialize_dao_factory
from tcl_api.repository.db.models import User, Deck, DeckViewer


@get_dao(User)
@get_dao(Deck)
@get_dao(DeckViewer)
class UserService:
    # type hints for injected DAOs to help IDE
    user_dao: 'UserDAO'
    deck_dao: 'DeckDAO'
    deckviewer_dao: 'DeckViewerDAO'

    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger("services.user")

        initialize_dao_factory(db)

    def _check_user_exists(self, user_id: UUID) -> User:
        """Check if user exists and is not deleted."""
        user = self.user_dao.get_by_id(user_id)
        if not user or user.deleted_at:
            self.logger.warning(f"User not found or deleted: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    def _check_email_exists(self, email: str) -> bool:
        """Check if email is already in use."""
        user = self.user_dao.get_by_email(email)
        return user is not None

    def create_user(
        self,
        email: str,
        name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> User:
        """Create a new user."""
        self.logger.debug(f"Creating user with email: {email}")

        # Check if user already exists
        if self._check_email_exists(email):
            self.logger.warning(f"User already exists with email: {email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )

        # Create user
        user_data = {
            "email": email,
            "name": name,
            "preferences": preferences or {}
        }
        user = self.user_dao.create(user_data)

        self.logger.info(f"Successfully created user: {user.user_id}")
        return user

    def get_user_by_id(self, user_id: UUID) -> Dict[str, Any]:
        """Get user profile by ID with deck counts."""
        self.logger.debug(f"Retrieving user: {user_id}")

        user = self._check_user_exists(user_id)

        # Count owned decks
        owned_count = self.deck_dao.count_by_owner(user.user_id)

        # Count shared decks
        shared_decks = self.deck_dao.get_shared_with_user(user.user_id)
        shared_count = len(shared_decks) if shared_decks else 0

        self.logger.info(f"Retrieved user: {user_id}")

        return user.serialize(owned_count, shared_count)

    def get_user_by_email(self, email: str) -> Dict[str, Any]:
        """Get user profile by email with deck counts."""
        self.logger.debug(f"Retrieving user by email: {email}")

        user = self.user_dao.get_by_email(email)
        if not user or user.deleted_at:
            self.logger.warning(f"User not found by email: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Count owned decks
        owned_count = self.deck_dao.count_by_owner(user.user_id)

        # Count shared decks
        shared_decks = self.deck_dao.get_shared_with_user(user.user_id)
        shared_count = len(shared_decks) if shared_decks else 0

        self.logger.info(f"Retrieved user by email: {email}")

        return user.serialize(owned_count, shared_count)

    def update_user(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update user profile."""
        self.logger.debug(f"Updating user: {user_id}")

        # Check user exists
        user = self._check_user_exists(user_id)

        # Prepare update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if preferences is not None:
            update_data["preferences"] = preferences

        if not update_data:
            self.logger.warning(f"No data to update for user: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )

        # Update user
        user = self.user_dao.update(user_id, update_data)

        # Count owned decks
        owned_count = self.deck_dao.count_by_owner(user.user_id)

        # Count shared decks
        shared_decks = self.deck_dao.get_shared_with_user(user.user_id)
        shared_count = len(shared_decks) if shared_decks else 0

        self.logger.info(f"Successfully updated user: {user_id}")

        return user.serialize(owned_count, shared_count)

    def delete_user(self, user_id: UUID) -> None:
        """Soft delete user account."""
        self.logger.debug(f"Deleting user: {user_id}")

        # Check user exists
        user = self._check_user_exists(user_id)

        # Soft delete user
        self.user_dao.soft_delete(user_id)

        self.logger.info(f"Successfully deleted user: {user_id}")

    def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List active users with optional search."""
        self.logger.debug(f"Listing users: skip={skip}, limit={limit}, search={search}")

        # Get users
        if search:
            users = self.user_dao.search_by_name_or_email(search, skip=skip, limit=limit)
        else:
            users = self.user_dao.get_active_users(skip=skip, limit=limit)

        # Serialize users
        result = []
        for user in users:
            # Count owned decks
            owned_count = self.deck_dao.count_by_owner(user.user_id)

            # Count shared decks
            shared_decks = self.deck_dao.get_shared_with_user(user.user_id)
            shared_count = len(shared_decks) if shared_decks else 0

            result.append(user.serialize(owned_count, shared_count))

        self.logger.info(f"Retrieved {len(result)} users")
        return result

    def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user statistics."""
        self.logger.debug(f"Getting stats for user: {user_id}")

        user = self._check_user_exists(user_id)

        # Count owned decks
        owned_decks = self.deck_dao.get_by_owner(user_id)
        owned_count = len(owned_decks) if owned_decks else 0

        # Count shared decks
        shared_decks = self.deck_dao.get_shared_with_user(user_id)
        shared_count = len(shared_decks) if shared_decks else 0

        self.logger.info(f"Retrieved stats for user: {user_id}")

        return {
            "user_id": str(user.user_id),
            "email": user.email,
            "owned_decks_count": owned_count,
            "shared_decks_count": shared_count,
            "total_decks": owned_count + shared_count,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }

