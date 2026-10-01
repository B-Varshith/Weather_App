"""FastAPI routes for the chat API."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse, SOPCitation
from app.graph.graph import advisory_graph
from app.repositories.session_repository import SessionRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

_session_repo = SessionRepository()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a user chat message through the advisory pipeline."""
    session_id = request.session_id
    message = request.message

    logger.info("session=%s message=%s", session_id, message[:100])

    # Store the user message in session
    _session_repo.add_message(session_id, "user", message)
    messages = _session_repo.get_messages(session_id)

    # Build initial graph state
    initial_state = {
        "session_id": session_id,
        "messages": messages,
        "user_query": message,
        "activity": None,
        "location_name": None,
        "latitude": None,
        "longitude": None,
        "requested_time": None,
        "user_context": {},
        "weather": None,
        "weather_raw": None,
        "matched_sops": [],
        "selected_sop": None,
        "decision_reason": None,
        "response": None,
        "error": None,
        "trace": [],
    }

    try:
        # Run the LangGraph
        result = await advisory_graph.ainvoke(initial_state)
    except Exception as e:
        logger.exception("Graph execution failed: %s", e)
        return ChatResponse(
            session_id=session_id,
            answer="I encountered an internal error processing your request. Please try again.",
            error="INTERNAL_ERROR",
            trace=[{"node": "graph", "status": "error", "data": {"reason": str(e)}}],
        )

    # Build response
    sop_citation = None
    selected = result.get("selected_sop")
    if selected:
        sop_citation = SOPCitation(
            id=selected.get("id"),
            name=selected.get("name"),
            severity=selected.get("severity"),
        )

    # Weather summary for the response
    weather_summary = None
    weather_data = result.get("weather")
    if weather_data:
        weather_summary = {
            "temperature_c": weather_data.get("temperature_c"),
            "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
            "precipitation_probability": weather_data.get("precipitation_probability"),
            "precipitation_mm": weather_data.get("precipitation_mm"),
            "uv_index": weather_data.get("uv_index"),
        }

    location_info = None
    if result.get("latitude") is not None:
        location_info = {
            "name": result.get("location_name"),
            "latitude": result.get("latitude"),
            "longitude": result.get("longitude"),
        }

    # Store decision
    _session_repo.add_decision(session_id, {
        "sop": sop_citation.model_dump() if sop_citation else None,
        "weather": weather_summary,
        "reason": result.get("decision_reason"),
    })

    return ChatResponse(
        session_id=session_id,
        answer=result.get("response", "I was unable to generate a response."),
        sop=sop_citation,
        weather=weather_summary,
        location=location_info,
        trace=result.get("trace", []),
        error=result.get("error"),
    )


@router.get("/session/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    """Debug endpoint — returns full session state."""
    return _session_repo.get_full_session(session_id)


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
