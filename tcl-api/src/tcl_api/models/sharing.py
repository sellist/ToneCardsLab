from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class ViewersResponse(BaseModel):
    deck_id: str = Field(..., description="UUID of the deck")
    viewer_ids: List[str] = Field(default_factory=list, description="List of user IDs with viewer access")


class EditViewersRequest(BaseModel):
    add_viewer_ids: List[str] = Field(
        default_factory=list,
        description="User IDs to add as viewers"
    )
    remove_viewer_ids: List[str] = Field(
        default_factory=list,
        description="User IDs to remove from viewers"
    )


class ShareByEmailRequest(BaseModel):
    recipient_email: EmailStr = Field(..., description="Email address of recipient")
    message: Optional[str] = Field(None, max_length=500, description="Optional invitation message")


class ShareByEmailResponse(BaseModel):
    invitation_id: str = Field(..., description="UUID of the invitation")
    status: str = Field(default="sent", description="Status of the invitation")
    expires_at: Optional[str] = Field(None, description="ISO 8601 timestamp when invitation expires")

