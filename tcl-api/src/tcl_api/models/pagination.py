from pydantic import BaseModel, Field
from typing import Dict, Any


class Pagination(BaseModel):

    skip: int = Field(default=0, ge=0, description="Number of items to skip (0-indexed)")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of items to return")

    @classmethod
    def from_page(cls, page: int = 1, page_size: int = 20) -> "Pagination":
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        skip = (page - 1) * page_size
        return cls(skip=skip, limit=page_size)

    @classmethod
    def from_skip_limit(cls, skip: int = 0, limit: int = 20) -> "Pagination":
        skip = max(0, skip)
        limit = max(1, min(limit, 100))
        return cls(skip=skip, limit=limit)

    @property
    def page(self) -> int:
        return (self.skip // self.limit) + 1

    @property
    def page_size(self) -> int:
        return self.limit

    @property
    def offset(self) -> int:
        return self.skip

    def to_dict(self) -> Dict[str, int]:
        return {"skip": self.skip, "limit": self.limit}

    def to_page_dict(self) -> Dict[str, int]:
        return {"page": self.page, "page_size": self.page_size}

    def get_sql_offset_limit(self) -> tuple[int, int]:
        return self.skip, self.limit

    def __repr__(self) -> str:
        return f"Pagination(page={self.page}, page_size={self.page_size}, skip={self.skip}, limit={self.limit})"


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_count: int = Field(..., ge=0, description="Total number of items across all pages")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")

    @classmethod
    def from_pagination_and_total(
        cls,
        pagination: Pagination,
        total_count: int
    ) -> "PaginationMeta":
        total_pages = (total_count + pagination.limit - 1) // pagination.limit
        has_next = pagination.page < total_pages
        has_previous = pagination.page > 1

        return cls(
            page=pagination.page,
            page_size=pagination.page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_count": self.total_count,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous
        }

