"""Pydantic models for decision trace and conflict resolution."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Any


class TraceEntry(BaseModel):
    """Single step in the decision trace."""
    node: str
    status: str = "success"
    data: Optional[dict[str, Any]] = None


class DecisionResult(BaseModel):
    """Outcome of the SOP conflict resolution step."""
    selected_sop_id: Optional[str] = None
    selected_sop_name: Optional[str] = None
    severity: Optional[str] = None
    reason: str = ""
    all_matched_ids: list[str] = []
