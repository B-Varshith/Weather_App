"""In-memory session repository for conversation context."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Simple in-memory store: session_id → list of message dicts
_sessions: dict[str, dict[str, Any]] = {}


class SessionRepository:
    """Stores conversation history per session_id (memory resets on restart)."""

    def get_session(self, session_id: str) -> dict[str, Any]:
        """Return or create a session object."""
        if session_id not in _sessions:
            _sessions[session_id] = {
                "messages": [],
                "decisions": [],
                "weather_requests": [],
                "sop_matches": [],
                "last_activity": None,
                "last_location": None,
                "last_time": None,
            }
            logger.info("Created new session: %s", session_id)
        return _sessions[session_id]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        session = self.get_session(session_id)
        session["messages"].append({"role": role, "content": content})

    def add_decision(self, session_id: str, decision: dict) -> None:
        session = self.get_session(session_id)
        session["decisions"].append(decision)

    def update_context(
        self,
        session_id: str,
        activity: Optional[str] = None,
        location: Optional[str] = None,
        time: Optional[str] = None,
    ) -> None:
        session = self.get_session(session_id)
        if activity:
            session["last_activity"] = activity
        if location:
            session["last_location"] = location
        if time:
            session["last_time"] = time

    def get_context(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        return {
            "last_activity": session.get("last_activity"),
            "last_location": session.get("last_location"),
            "last_time": session.get("last_time"),
        }

    def get_messages(self, session_id: str) -> list[dict[str, str]]:
        session = self.get_session(session_id)
        return session.get("messages", [])

    def get_full_session(self, session_id: str) -> dict[str, Any]:
        return self.get_session(session_id)
