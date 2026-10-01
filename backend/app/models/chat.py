"""Pydantic models for chat request / response contracts."""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
import uuid


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 2000:
            raise ValueError("Message exceeds maximum length of 2000 characters")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()


class SOPCitation(BaseModel):
    """SOP reference included in a response."""
    id: Optional[str] = None
    name: Optional[str] = None
    severity: Optional[str] = None


class ChatResponse(BaseModel):
    """Outgoing response from the backend to the frontend."""
    session_id: str
    answer: str
    sop: Optional[SOPCitation] = None
    weather: Optional[dict[str, Any]] = None
    location: Optional[dict[str, Any]] = None
    trace: list[dict[str, Any]] = []
    error: Optional[str] = None
