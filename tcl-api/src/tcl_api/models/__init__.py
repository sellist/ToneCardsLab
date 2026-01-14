"""
Models package - centralized exports for all models.

Organized by category:
- entities: Database models (SQLModel with table=True)
- dto: Data Transfer Objects for API requests/responses
- auth: Authentication models
- file: File upload models
- response: API response wrappers
- builders: Response builders
- pagination: Pagination models
- common: Shared/reusable models
- enum: Enumerations
"""

# Database entities
from tcl_api.models.db.entities import (
    User,
    Deck,
    Card,
    DeckViewer,
    DeckInvitation,
    UploadedFile,
    ContentReport,
    DeckModeration,
    AuthToken,
    DeckStatistics,
    GUID,
    utcnow,
)

# DTOs
from tcl_api.models.dto import (
    UserCreate,
    UserUpdate,
    UserRead,
    UserDeleteConfirm,
    CardCreate,
    CardUpdate,
    CardRead,
    ReorderCardsRequest,
    DeckCreate,
    DeckUpdate,
    DeckSummary,
    DeckRead,
    DeckExportRequest,
    DeckImportRequest,
    BulkDeleteDecksRequest,
    TogglePublicStatusRequest,
    ViewersResponse,
    EditViewersRequest,
    ShareByEmailRequest,
    ShareByEmailResponse,
    ReportRequest,
)

# Auth models
from tcl_api.models.auth import (
    LoginRequest,
    TokenResponse,
    LoginResponse,
    RefreshTokenRequest,
    LogoutRequest,
)

# File models
from tcl_api.models.file import (
    UploadFileRequest,
    FileRead,
    UserFilesResponse,
    DeleteFileRequest,
)

# Response models
from tcl_api.models.response import (
    ApiResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse,
    Metadata,
)

# Builders
from tcl_api.models.builders import ApiResponseBuilder

# Pagination
from tcl_api.models.pagination import (
    Pagination,
    PaginationMeta,
)

# Common models
from tcl_api.models.common import (
    ResponseStatus,
    ErrorDetail
)

# Enums
from tcl_api.models.enum import (
    RendererType,
    DeckExportFormat,
)

# Mappers
from tcl_api.models.mappers import (
    user_to_read,
    card_to_read,
    deck_to_read,
    deck_to_summary,
    file_to_read,
    invitation_to_dict,
)

__all__ = [
    # Entities
    "User",
    "Deck",
    "Card",
    "DeckViewer",
    "DeckInvitation",
    "UploadedFile",
    "ContentReport",
    "DeckModeration",
    "AuthToken",
    "DeckStatistics",
    "GUID",
    "utcnow",
    # DTOs
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserDeleteConfirm",
    "CardCreate",
    "CardUpdate",
    "CardRead",
    "ReorderCardsRequest",
    "DeckCreate",
    "DeckUpdate",
    "DeckSummary",
    "DeckRead",
    "DeckExportRequest",
    "DeckImportRequest",
    "BulkDeleteDecksRequest",
    "TogglePublicStatusRequest",
    "ViewersResponse",
    "EditViewersRequest",
    "ShareByEmailRequest",
    "ShareByEmailResponse",
    "ReportRequest",
    # Auth
    "LoginRequest",
    "TokenResponse",
    "LoginResponse",
    "RefreshTokenRequest",
    "LogoutRequest",
    # Files
    "UploadFileRequest",
    "FileRead",
    "UserFilesResponse",
    "DeleteFileRequest",
    # Response
    "ApiResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "HealthResponse",
    "Metadata",
    # Builders
    "ApiResponseBuilder",
    # Pagination
    "Pagination",
    "PaginationMeta",
    # Common
    "ResponseStatus",
    "ErrorDetail",
    # Enums
    "RendererType",
    "DeckExportFormat",
    # Mappers
    "user_to_read",
    "card_to_read",
    "deck_to_read",
    "deck_to_summary",
    "file_to_read",
    "invitation_to_dict",
]

