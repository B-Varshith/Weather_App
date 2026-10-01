"""LangGraph node implementations for the advisory pipeline.

Each node performs a single step and updates the shared AdvisoryState.
The LLM is used ONLY in classify_intent (extraction) and compose_response
(language generation) — never for policy decisions.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.utils import extract_text
from app.graph.state import AdvisoryState
from app.services.location_service import LocationService
from app.services.geocoding_service import LocationResolutionError
from app.services.weather_service import WeatherService, WeatherFetchError
from app.services.sop_engine import evaluate_all_sops, resolve_conflicts
from app.services.response_service import ResponseService
from app.repositories.sop_repository import SOPRepository
from app.repositories.session_repository import SessionRepository

logger = logging.getLogger(__name__)

# Shared service instances
_location_service = LocationService()
_weather_service = WeatherService()
_sop_repo = SOPRepository()
_session_repo = SessionRepository()
_response_service = ResponseService()


def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        max_output_tokens=512,
    )


# ─── Node 1: classify_intent ──────────────────────────────────────────

INTENT_SYSTEM_PROMPT = """You are an intent extractor for a weather-advisory system.

Given a user's question, extract:
- activity_category: the outdoor activity (e.g., cycling, running, dog_walking, picnic, travel, driving, outdoor_play, hiking, walking)
- location: the city or location mentioned (null if not mentioned)
- requested_time: when they want to do it (e.g., "today", "this afternoon", "evening", null if not specified)
- user_group: if a specific group is mentioned (child, elderly, null if not applicable)

IMPORTANT:
- Map synonyms: "bike" → cycling, "ride my bike" → cycling, "drive" → travel, "walk my dog" → dog_walking
- "take my child to the park" → activity=outdoor_play, user_group=child
- "picnic" → activity=picnic
- Do NOT provide safety advice. Only extract intent.

Respond ONLY with valid JSON, no other text:
{
  "activity_category": "string or null",
  "location": "string or null",
  "requested_time": "string or null",
  "user_group": "string or null"
}"""


async def classify_intent(state: AdvisoryState) -> AdvisoryState:
    """Extract structured intent from the user's natural-language query."""
    query = state.get("user_query", "")
    session_id = state.get("session_id", "")
    messages = state.get("messages", [])

    # Build conversation context for the LLM
    context_msgs = []
    for m in messages[-6:]:  # Last 3 turns
        context_msgs.append(f"{m['role']}: {m['content']}")
    context_str = "\n".join(context_msgs)

    # Also include previous session context
    prev_context = _session_repo.get_context(session_id)

    user_prompt = f"""Previous conversation context:
{context_str}

Previous session context:
- Last activity: {prev_context.get('last_activity', 'none')}
- Last location: {prev_context.get('last_location', 'none')}
- Last time: {prev_context.get('last_time', 'none')}

Current user message: "{query}"

Extract the intent. If the user refers to a previous activity/location without repeating it, use the previous session context.
Respond with JSON only."""

    llm = _get_llm()
    response = await llm.ainvoke([
        SystemMessage(content=INTENT_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])

    content = ""
    try:
        # Clean the response — strip markdown code fences if present
        content = extract_text(response.content).strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            if content.startswith("json"):
                content = content[4:].strip()
        intent = json.loads(content)
    except (json.JSONDecodeError, Exception) as e:
        logger.error("Failed to parse intent: %s — raw: %s", e, content)
        intent = {
            "activity_category": None,
            "location": None,
            "requested_time": None,
            "user_group": None,
        }

    activity = intent.get("activity_category")
    location = intent.get("location")
    requested_time = intent.get("requested_time")
    user_group = intent.get("user_group")

    # Fall back to session context if not extracted
    if not activity and prev_context.get("last_activity"):
        activity = prev_context["last_activity"]
    if not location and prev_context.get("last_location"):
        location = prev_context["last_location"]

    # Update session context
    _session_repo.update_context(session_id, activity=activity, location=location, time=requested_time)

    trace = state.get("trace", [])
    trace.append({
        "node": "classify_intent",
        "status": "success",
        "data": {"activity": activity, "location": location, "time": requested_time, "user_group": user_group},
    })

    logger.info("session=%s intent: activity=%s location=%s time=%s group=%s",
                session_id, activity, location, requested_time, user_group)

    return {
        **state,
        "activity": activity,
        "location_name": location,
        "requested_time": requested_time,
        "user_context": {"group": user_group} if user_group else {},
        "trace": trace,
    }


# ─── Node 2: resolve_location ─────────────────────────────────────────

async def resolve_location(state: AdvisoryState) -> AdvisoryState:
    """Resolve the extracted location name to coordinates."""
    location_name = state.get("location_name")
    trace = state.get("trace", [])

    if not location_name:
        trace.append({"node": "resolve_location", "status": "failure", "data": {"reason": "No location provided"}})
        return {
            **state,
            "error": "LOCATION_MISSING",
            "trace": trace,
        }

    try:
        loc = await _location_service.resolve(location_name)
        trace.append({
            "node": "resolve_location",
            "status": "success",
            "data": {"name": loc.name, "lat": loc.latitude, "lon": loc.longitude},
        })
        return {
            **state,
            "location_name": loc.name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "trace": trace,
        }
    except LocationResolutionError as e:
        logger.warning("Location resolution failed: %s", e)
        trace.append({"node": "resolve_location", "status": "failure", "data": {"reason": str(e)}})
        return {
            **state,
            "error": "LOCATION_RESOLUTION_FAILED",
            "trace": trace,
        }


# ─── Node 3: fetch_weather ────────────────────────────────────────────

async def fetch_weather(state: AdvisoryState) -> AdvisoryState:
    """Fetch live weather data from Open-Meteo."""
    lat = state.get("latitude")
    lon = state.get("longitude")
    location_name = state.get("location_name", "unknown")
    trace = state.get("trace", [])

    if lat is None or lon is None:
        trace.append({"node": "fetch_weather", "status": "skipped", "data": {"reason": "No coordinates"}})
        return {**state, "trace": trace}

    try:
        from app.models.weather import LocationData
        loc = LocationData(name=location_name, latitude=lat, longitude=lon)
        weather = await _weather_service.get_weather(lat, lon, loc)
        weather_dict = weather.model_dump()

        trace.append({"node": "fetch_weather", "status": "success"})
        return {
            **state,
            "weather": weather_dict,
            "weather_raw": weather_dict,
            "trace": trace,
        }
    except WeatherFetchError as e:
        logger.warning("Weather fetch failed: %s", e)
        trace.append({"node": "fetch_weather", "status": "failure", "data": {"reason": str(e)}})
        return {
            **state,
            "error": "WEATHER_UNAVAILABLE",
            "trace": trace,
        }


# ─── Node 4: evaluate_sops ────────────────────────────────────────────

async def evaluate_sops(state: AdvisoryState) -> AdvisoryState:
    """Evaluate all SOPs against weather facts + intent (deterministic)."""
    weather_dict = state.get("weather")
    activity = state.get("activity")
    user_context = state.get("user_context", {})
    trace = state.get("trace", [])

    if not weather_dict:
        trace.append({"node": "evaluate_sops", "status": "skipped", "data": {"reason": "No weather data"}})
        return {**state, "trace": trace}

    # Reconstruct WeatherData from dict
    from app.models.weather import WeatherData
    weather = WeatherData(**weather_dict)

    intent = {
        "activity_category": activity,
        "user_group": user_context.get("group"),
    }

    sops = _sop_repo.get_all()
    matches = evaluate_all_sops(sops, weather, intent)

    matched_ids = [m.sop.id for m in matches]
    trace.append({
        "node": "evaluate_sops",
        "status": "success",
        "matched": matched_ids,
    })

    logger.info("SOP evaluation: matched=%s", matched_ids)

    return {
        **state,
        "matched_sops": [{"id": m.sop.id, "name": m.sop.name, "severity": m.sop.severity,
                          "priority": m.sop.priority, "guidance": m.sop.guidance,
                          "reason": m.reason} for m in matches],
        "trace": trace,
    }


# ─── Node 5: resolve_conflicts ────────────────────────────────────────

async def resolve_conflicts_node(state: AdvisoryState) -> AdvisoryState:
    """Deterministic conflict resolution among matching SOPs."""
    matched_sops = state.get("matched_sops", [])
    trace = state.get("trace", [])

    if not matched_sops:
        trace.append({"node": "resolve_conflicts", "status": "no_match"})
        return {
            **state,
            "selected_sop": None,
            "decision_reason": "No SOP matched the current conditions",
            "trace": trace,
        }

    # Re-create SOPMatch objects for conflict resolution
    from app.models.sop import SOP, SOPMatch
    sop_matches = []
    for m in matched_sops:
        sop = _sop_repo.get_by_id(m["id"])
        if sop:
            sop_matches.append(SOPMatch(sop=sop, matched=True, reason=m.get("reason", "")))

    winner = resolve_conflicts(sop_matches)

    if winner:
        selected = {
            "id": winner.sop.id,
            "name": winner.sop.name,
            "severity": winner.sop.severity,
            "guidance": winner.sop.guidance,
            "rationale": winner.sop.rationale,
        }
        trace.append({"node": "resolve_conflicts", "selected": winner.sop.id, "status": "success"})
        return {
            **state,
            "selected_sop": selected,
            "decision_reason": winner.reason,
            "trace": trace,
        }

    trace.append({"node": "resolve_conflicts", "status": "no_winner"})
    return {**state, "selected_sop": None, "trace": trace}


# ─── Node 6: compose_response ─────────────────────────────────────────

async def compose_response(state: AdvisoryState) -> AdvisoryState:
    """Use the LLM to compose a natural-language response from facts."""
    selected_sop = state.get("selected_sop")
    weather = state.get("weather", {})
    user_query = state.get("user_query", "")
    activity = state.get("activity")
    location_name = state.get("location_name")
    trace = state.get("trace", [])

    if selected_sop:
        # Compose advisory with SOP
        weather_summary = {
            "temperature_c": weather.get("temperature_c"),
            "wind_speed_kmh": weather.get("wind_speed_kmh"),
            "wind_gusts_kmh": weather.get("wind_gusts_kmh"),
            "precipitation_mm": weather.get("precipitation_mm"),
            "precipitation_probability": weather.get("precipitation_probability"),
            "uv_index": weather.get("uv_index"),
            "weather_code": weather.get("weather_code"),
        }
        answer = await _response_service.compose_advisory(
            user_query=user_query,
            weather=weather_summary,
            selected_sop=selected_sop,
            activity=activity,
            location_name=location_name,
            decision_reason=state.get("decision_reason"),
            latitude=state.get("latitude"),
            longitude=state.get("longitude"),
        )
    else:
        # No SOP matched
        answer = await _response_service.compose_no_sop(
            user_query=user_query,
            weather=weather,
            location_name=location_name,
        )

    trace.append({"node": "compose_response", "status": "success"})

    # Store in session
    session_id = state.get("session_id", "")
    _session_repo.add_message(session_id, "assistant", answer)

    return {**state, "response": answer, "trace": trace}


# ─── Failure nodes ─────────────────────────────────────────────────────

async def location_failure(state: AdvisoryState) -> AdvisoryState:
    """Handle location resolution failure."""
    user_query = state.get("user_query", "")
    location_name = state.get("location_name")
    trace = state.get("trace", [])

    answer = await _response_service.compose_location_failure(user_query, location_name)
    trace.append({"node": "location_failure", "status": "handled"})

    session_id = state.get("session_id", "")
    _session_repo.add_message(session_id, "assistant", answer)

    return {**state, "response": answer, "trace": trace}


async def weather_failure(state: AdvisoryState) -> AdvisoryState:
    """Handle weather fetch failure."""
    user_query = state.get("user_query", "")
    location_name = state.get("location_name")
    trace = state.get("trace", [])

    answer = await _response_service.compose_weather_failure(user_query, location_name)
    trace.append({"node": "weather_failure", "status": "handled"})

    session_id = state.get("session_id", "")
    _session_repo.add_message(session_id, "assistant", answer)

    return {**state, "response": answer, "error": "WEATHER_UNAVAILABLE", "trace": trace}


async def no_sop_fallback(state: AdvisoryState) -> AdvisoryState:
    """Handle case when no SOP applies."""
    return await compose_response(state)
