from .health import HealthResponse
from .response import ApiResponse, ErrorResponse, PaginatedResponse, Metadata

# Common models
from .common import (
    ResponseStatus,
    ErrorDetail,
    ApiResponse as CommonApiResponse,
    PaginationParams,
    PaginatedResponse as CommonPaginatedResponse,
    TokenResponse,
    TimestampMixin,
    OwnershipMixin,
    IdResponse,
    SearchParams,
    ReportRequest,
)

# Auth models
from .auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    LogoutRequest
)

# User models
from .user import (
    User,
    UserCreate,
    UserUpdate,
    UserDeleteConfirm
)

# Card models
from .card import (
    RendererType,
    CardBase,
    CardCreate,
    CardUpdate,
    Card,
    ReorderCardsRequest
)

# Deck models
from .deck import (
    DeckBase,
    DeckCreate,
    DeckUpdate,
    DeckSummary,
    Deck,
    DeckExportFormat,
    DeckExportRequest,
    DeckImportRequest,
    BulkDeleteDecksRequest,
    TogglePublicStatusRequest
)

# Sharing models
from .sharing import (
    ViewersResponse,
    EditViewersRequest,
    ShareByEmailRequest,
    ShareByEmailResponse
)

# File models
from .file import (
    UploadFileRequest,
    UploadedFile,
    UserFilesResponse,
    DeleteFileRequest
)

__all__ = [
    # Legacy models
    "HealthResponse",
    "ApiResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "Metadata",

    # Common models
    "ResponseStatus",
    "ErrorDetail",
    "CommonApiResponse",
    "PaginationParams",
    "CommonPaginatedResponse",
    "TokenResponse",
    "TimestampMixin",
    "OwnershipMixin",
    "IdResponse",
    "SearchParams",
    "ReportRequest",

    # Auth models
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "LogoutRequest",

    # User models
    "User",
    "UserCreate",
    "UserUpdate",
    "UserDeleteConfirm",

    # Card models
    "RendererType",
    "CardBase",
    "CardCreate",
    "CardUpdate",
    "Card",
    "ReorderCardsRequest",

    # Deck models
    "DeckBase",
    "DeckCreate",
    "DeckUpdate",
    "DeckSummary",
    "Deck",
    "DeckExportFormat",
    "DeckExportRequest",
    "DeckImportRequest",
    "BulkDeleteDecksRequest",
    "TogglePublicStatusRequest",

    # Sharing models
    "ViewersResponse",
    "EditViewersRequest",
    "ShareByEmailRequest",
    "ShareByEmailResponse",

    # File models
    "UploadFileRequest",
    "UploadedFile",
    "UserFilesResponse",
    "DeleteFileRequest",
]
