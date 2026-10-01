"""LangGraph state definition for the advisory pipeline."""

from __future__ import annotations
from typing import TypedDict, Any, Optional


class AdvisoryState(TypedDict, total=False):
    """Strongly-typed state passed through the LangGraph pipeline."""

    # Session
    session_id: str
    messages: list[dict[str, str]]

    # User input
    user_query: str

    # Extracted intent
    activity: Optional[str]
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    requested_time: Optional[str]
    user_context: dict[str, Any]

    # Weather data
    weather: Optional[dict[str, Any]]
    weather_raw: Optional[dict[str, Any]]

    # SOP evaluation
    matched_sops: list[dict[str, Any]]
    selected_sop: Optional[dict[str, Any]]
    decision_reason: Optional[str]

    # Output
    response: Optional[str]
    error: Optional[str]

    # Trace
    trace: list[dict[str, Any]]
