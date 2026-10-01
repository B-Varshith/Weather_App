"""LLM-based response composition service.

The LLM receives ONLY structured facts (weather data + selected SOP)
and composes a natural-language response.  It CANNOT override the
policy decision or invent weather values.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.prompts.response_prompt import (
    RESPONSE_SYSTEM_PROMPT,
    build_response_user_prompt,
    FALLBACK_NO_SOP_PROMPT,
    WEATHER_FAILURE_PROMPT,
    LOCATION_FAILURE_PROMPT,
)

logger = logging.getLogger(__name__)


def _get_llm() -> ChatGoogleGenerativeAI:
    """Create an LLM instance from config."""
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.3,
        max_output_tokens=1024,
    )


class ResponseService:
    """Composes natural-language responses using the LLM."""

    def __init__(self):
        self.llm = _get_llm()

    async def compose_advisory(
        self,
        user_query: str,
        weather: dict[str, Any],
        selected_sop: dict[str, Any],
        activity: str | None = None,
        location_name: str | None = None,
    ) -> str:
        """Compose a policy-grounded advisory response."""
        user_prompt = build_response_user_prompt(
            user_query=user_query,
            weather=weather,
            selected_sop=selected_sop,
            activity=activity,
            location_name=location_name,
        )
        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content

    async def compose_no_sop(self, user_query: str, weather: dict[str, Any], location_name: str | None = None) -> str:
        """Compose a response when no SOP applies."""
        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=FALLBACK_NO_SOP_PROMPT.format(
                user_query=user_query,
                weather=weather,
                location=location_name or "unknown",
            )),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content

    async def compose_weather_failure(self, user_query: str, location_name: str | None = None) -> str:
        """Compose a response when weather data cannot be fetched."""
        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=WEATHER_FAILURE_PROMPT.format(
                user_query=user_query,
                location=location_name or "the requested location",
            )),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content

    async def compose_location_failure(self, user_query: str, location_name: str | None = None) -> str:
        """Compose a response when the location cannot be resolved."""
        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=LOCATION_FAILURE_PROMPT.format(
                user_query=user_query,
                location=location_name or "the requested location",
            )),
        ]
        response = await self.llm.ainvoke(messages)
        return response.content
