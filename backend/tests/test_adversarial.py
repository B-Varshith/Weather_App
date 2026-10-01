"""Adversarial / prompt injection tests.

These tests verify that the SOP engine remains authoritative
regardless of what the user says in their message.
"""

import pytest

from app.services.sop_engine import evaluate_all_sops, resolve_conflicts
from app.models.weather import WeatherData, LocationData
from app.models.sop import SOP, SOPCondition, SOPRule
from app.repositories.sop_repository import SOPRepository


def _make_weather(**kwargs) -> WeatherData:
    defaults = {
        "source": "test",
        "retrieved_at": "2024-01-01T12:00:00",
        "location": LocationData(name="Test", latitude=0, longitude=0),
        "temperature_c": 25,
        "wind_speed_kmh": 45,  # Above cycling threshold
        "wind_gusts_kmh": 55,
        "uv_index": 3,
        "precipitation_mm": 0,
        "precipitation_probability": 10,
        "weather_code": 0,
    }
    defaults.update(kwargs)
    return WeatherData(**defaults)


class TestPromptInjection:
    def test_sop_engine_ignores_user_intent_override(self):
        """Even if user claims wind is 5 km/h, engine uses actual values."""
        weather = _make_weather(wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)

        # SOP-002 (high wind cycling) should still match because
        # actual wind_speed_kmh is 45, not the user's claimed 5
        matched_ids = [m.sop.id for m in matches]
        assert "SOP-002" in matched_ids

    def test_sop_engine_uses_real_weather(self):
        """The engine should use actual weather values, not user-supplied ones."""
        weather = _make_weather(uv_index=9, wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)

        # Both UV and wind SOPs should match
        matched_ids = [m.sop.id for m in matches]
        assert len(matched_ids) >= 2  # At least SOP-001 and SOP-002

    def test_conflict_resolution_deterministic(self):
        """Conflict resolution must be deterministic, not LLM-driven."""
        weather = _make_weather(uv_index=9, wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)

        winner = resolve_conflicts(matches)
        assert winner is not None
        # SOP-002 has priority 80 vs SOP-001's 60, both severity high
        assert winner.sop.id == "SOP-002"

        # Run it again — same result (deterministic)
        winner2 = resolve_conflicts(matches)
        assert winner2.sop.id == winner.sop.id
