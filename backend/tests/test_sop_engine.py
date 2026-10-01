"""Unit tests for the deterministic SOP engine."""

import pytest

from app.services.sop_engine import (
    evaluate_condition,
    evaluate_all_sops,
    resolve_conflicts,
    _build_facts,
    _detect_severe,
)
from app.models.sop import SOP, SOPCondition, SOPRule, SOPMatch
from app.models.weather import WeatherData, LocationData


# ─── evaluate_condition tests ──────────────────────────────────────────

class TestEvaluateCondition:
    def test_eq(self):
        assert evaluate_condition("cycling", "eq", "cycling") is True
        assert evaluate_condition("running", "eq", "cycling") is False

    def test_neq(self):
        assert evaluate_condition("running", "neq", "cycling") is True

    def test_gt(self):
        assert evaluate_condition(45, "gt", 40) is True
        assert evaluate_condition(40, "gt", 40) is False

    def test_gte(self):
        assert evaluate_condition(40, "gte", 40) is True
        assert evaluate_condition(39, "gte", 40) is False

    def test_lt(self):
        assert evaluate_condition(30, "lt", 40) is True

    def test_lte(self):
        assert evaluate_condition(40, "lte", 40) is True

    def test_in_list(self):
        assert evaluate_condition("cycling", "in", ["cycling", "running"]) is True
        assert evaluate_condition("swimming", "in", ["cycling", "running"]) is False

    def test_not_in(self):
        assert evaluate_condition("swimming", "not_in", ["cycling", "running"]) is True

    def test_contains(self):
        assert evaluate_condition("thunderstorm warning", "contains", "thunder") is True

    def test_between(self):
        assert evaluate_condition(35, "between", [30, 40]) is True
        assert evaluate_condition(45, "between", [30, 40]) is False

    def test_none_value(self):
        assert evaluate_condition(None, "gte", 40) is False


# ─── SOP evaluation tests ─────────────────────────────────────────────

def _make_weather(**kwargs) -> WeatherData:
    defaults = {
        "source": "test",
        "retrieved_at": "2024-01-01T12:00:00",
        "location": LocationData(name="Test", latitude=0, longitude=0),
        "temperature_c": 25,
        "wind_speed_kmh": 10,
        "uv_index": 3,
        "precipitation_mm": 0,
        "precipitation_probability": 10,
        "weather_code": 0,
    }
    defaults.update(kwargs)
    return WeatherData(**defaults)


def _make_sop(sop_id: str, severity: str, priority: int, rule: SOPRule) -> SOP:
    return SOP(
        id=sop_id,
        name=f"Test {sop_id}",
        category="test",
        severity=severity,
        applies_when=rule,
        guidance=["Test guidance"],
        priority=priority,
    )


class TestSOPEvaluation:
    def test_high_wind_cycling_match(self):
        """SOP-002 should match when wind >= 40 and activity is cycling."""
        weather = _make_weather(wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        rule = SOPRule(all=[
            SOPCondition(field="wind_speed_kmh", operator="gte", value=40),
            SOPCondition(field="activity_category", operator="in", value=["cycling", "biking"]),
        ])
        sop = _make_sop("SOP-002", "high", 80, rule)

        from app.services.sop_engine import evaluate_sop
        result = evaluate_sop(sop, weather, intent)
        assert result.matched is True

    def test_high_wind_cycling_no_match(self):
        """SOP-002 should NOT match when wind < 40."""
        weather = _make_weather(wind_speed_kmh=30)
        intent = {"activity_category": "cycling"}

        rule = SOPRule(all=[
            SOPCondition(field="wind_speed_kmh", operator="gte", value=40),
            SOPCondition(field="activity_category", operator="in", value=["cycling"]),
        ])
        sop = _make_sop("SOP-002", "high", 80, rule)

        from app.services.sop_engine import evaluate_sop
        result = evaluate_sop(sop, weather, intent)
        assert result.matched is False

    def test_uv_outdoor_exercise_match(self):
        """SOP-001 should match when UV >= 8 and activity is outdoor exercise."""
        weather = _make_weather(uv_index=9)
        intent = {"activity_category": "running"}

        rule = SOPRule(all=[
            SOPCondition(field="uv_index", operator="gte", value=8),
            SOPCondition(field="activity_category", operator="in", value=["running", "cycling"]),
        ])
        sop = _make_sop("SOP-001", "high", 60, rule)

        from app.services.sop_engine import evaluate_sop
        result = evaluate_sop(sop, weather, intent)
        assert result.matched is True


class TestConflictResolution:
    def test_critical_beats_high(self):
        """Critical severity should win over high."""
        sop_high = _make_sop("SOP-A", "high", 80, SOPRule(all=[]))
        sop_crit = _make_sop("SOP-B", "critical", 50, SOPRule(all=[]))

        matches = [
            SOPMatch(sop=sop_high, matched=True),
            SOPMatch(sop=sop_crit, matched=True),
        ]

        winner = resolve_conflicts(matches)
        assert winner is not None
        assert winner.sop.id == "SOP-B"

    def test_same_severity_priority_wins(self):
        """When severity is equal, higher priority wins."""
        sop_low_pri = _make_sop("SOP-A", "high", 50, SOPRule(all=[]))
        sop_high_pri = _make_sop("SOP-B", "high", 80, SOPRule(all=[]))

        matches = [
            SOPMatch(sop=sop_low_pri, matched=True),
            SOPMatch(sop=sop_high_pri, matched=True),
        ]

        winner = resolve_conflicts(matches)
        assert winner is not None
        assert winner.sop.id == "SOP-B"

    def test_no_matches(self):
        """Empty matches should return None."""
        assert resolve_conflicts([]) is None

    def test_single_match(self):
        """Single match should be returned directly."""
        sop = _make_sop("SOP-A", "high", 50, SOPRule(all=[]))
        matches = [SOPMatch(sop=sop, matched=True)]
        winner = resolve_conflicts(matches)
        assert winner is not None
        assert winner.sop.id == "SOP-A"


class TestSevereWeatherDetection:
    def test_thunderstorm_code(self):
        weather = _make_weather(weather_code=95)
        assert _detect_severe(weather) is True

    def test_extreme_precipitation(self):
        weather = _make_weather(precipitation_mm=25)
        assert _detect_severe(weather) is True

    def test_extreme_gusts(self):
        weather = _make_weather(wind_gusts_kmh=90)
        assert _detect_severe(weather) is True

    def test_normal_weather(self):
        weather = _make_weather()
        assert _detect_severe(weather) is False
