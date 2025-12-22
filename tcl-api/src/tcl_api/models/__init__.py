"""
Models package - unified SQLModel entities for database and API.

All table models (User, Deck, Card, etc.) work as both:
- SQLAlchemy ORM models for database operations
- Pydantic models for API validation

Request/Response models (UserCreate, DeckRead, etc.) are API-only Pydantic models.
"""

# Database table models (SQLModel with table=True)
from .entities import (
    # Core entities
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

    # Enums
    RendererType,
    DeckExportFormat,

    # Custom types
    GUID,
)

# API request/response models
from .entities import (
    # User
    UserCreate,
    UserUpdate,
    UserRead,
    UserDeleteConfirm,

    # Card
    CardCreate,
    CardUpdate,
    CardRead,
    ReorderCardsRequest,

    # Deck
    DeckCreate,
    DeckUpdate,
    DeckSummary,
    DeckRead,
    DeckExportRequest,
    DeckImportRequest,
    BulkDeleteDecksRequest,
    TogglePublicStatusRequest,

    # Sharing
    ViewersResponse,
    EditViewersRequest,
    ShareByEmailRequest,
    ShareByEmailResponse,

    # File
    UploadFileRequest,
    FileRead,
    UserFilesResponse,
    DeleteFileRequest,

    # Auth
    LoginRequest,
    TokenResponse,
    LoginResponse,
    RefreshTokenRequest,
    LogoutRequest,

    # Reports
    ReportRequest,
)

# Common models (keep for backward compatibility)
from .common import (
    ResponseStatus,
    ErrorDetail,
    ApiResponse,
    PaginationParams,
    PaginatedResponse,
    TimestampMixin,
    OwnershipMixin,
    IdResponse,
    SearchParams,
)

from .response import (
    ApiResponse as ApiResponseWrapper,
    ErrorResponse,
    PaginatedResponse as PaginatedResponseWrapper,
    Metadata,
)

from .health import HealthResponse
from .pagination import Pagination, PaginationMeta

__all__ = [
    # Database models
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

    # Enums
    "RendererType",
    "DeckExportFormat",

    # Custom types
    "GUID",

    # User API models
    "UserCreate",
    "UserUpdate",
    "UserRead",
    "UserDeleteConfirm",

    # Card API models
    "CardCreate",
    "CardUpdate",
    "CardRead",
    "ReorderCardsRequest",

    # Deck API models
    "DeckCreate",
    "DeckUpdate",
    "DeckSummary",
    "DeckRead",
    "DeckExportRequest",
    "DeckImportRequest",
    "BulkDeleteDecksRequest",
    "TogglePublicStatusRequest",

    # Sharing API models
    "ViewersResponse",
    "EditViewersRequest",
    "ShareByEmailRequest",
    "ShareByEmailResponse",

    # File API models
    "UploadFileRequest",
    "FileRead",
    "UserFilesResponse",
    "DeleteFileRequest",

    # Auth API models
    "LoginRequest",
    "TokenResponse",
    "LoginResponse",
    "RefreshTokenRequest",
    "LogoutRequest",

    # Reports
    "ReportRequest",

    # Common/Response models
    "ResponseStatus",
    "ErrorDetail",
    "ApiResponse",
    "PaginationParams",
    "PaginatedResponse",
    "TimestampMixin",
    "OwnershipMixin",
    "IdResponse",
    "SearchParams",
    "ApiResponseWrapper",
    "ErrorResponse",
    "PaginatedResponseWrapper",
    "Metadata",
    "HealthResponse",
    "Pagination",
    "PaginationMeta",
]
