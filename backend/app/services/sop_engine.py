"""Deterministic SOP evaluation engine.

This module is the heart of the policy system.  It evaluates structured
weather facts + user intent against every SOP condition using pure
deterministic logic — the LLM never participates in this step.
"""

from __future__ import annotations

import logging
from typing import Any, Union

from app.models.sop import SOP, SOPCondition, SOPRule, SOPMatch
from app.models.weather import WeatherData

logger = logging.getLogger(__name__)

# Severity ordering for conflict resolution
SEVERITY_ORDER = {"critical": 4, "high": 3, "moderate": 2, "low": 1}

# Weather codes that indicate thunderstorm (WMO)
THUNDERSTORM_CODES = {95, 96, 99}

# Weather codes that indicate severe weather
SEVERE_WEATHER_CODES = {65, 67, 75, 77, 82, 85, 86, 95, 96, 99}


def evaluate_condition(actual: Any, operator: str, expected: Any) -> bool:
    """Evaluate a single condition clause deterministically.

    Supports: eq, neq, gt, gte, lt, lte, in, not_in, contains, between
    """
    if actual is None:
        return False

    try:
        if operator == "eq":
            return actual == expected
        if operator == "neq":
            return actual != expected
        if operator == "gt":
            return float(actual) > float(expected)
        if operator == "gte":
            return float(actual) >= float(expected)
        if operator == "lt":
            return float(actual) < float(expected)
        if operator == "lte":
            return float(actual) <= float(expected)
        if operator == "in":
            if isinstance(expected, list):
                return actual in expected
            return str(actual) in str(expected)
        if operator == "not_in":
            if isinstance(expected, list):
                return actual not in expected
            return str(actual) not in str(expected)
        if operator == "contains":
            return str(expected).lower() in str(actual).lower()
        if operator == "between":
            if isinstance(expected, list) and len(expected) == 2:
                return float(expected[0]) <= float(actual) <= float(expected[1])
            return False
    except (ValueError, TypeError):
        return False

    logger.warning("Unknown operator: %s", operator)
    return False


def _build_facts(weather: WeatherData, intent: dict[str, Any]) -> dict[str, Any]:
    """Flatten weather + intent into a single facts dict for condition lookup."""
    facts: dict[str, Any] = {}

    # Weather facts
    if weather:
        facts["temperature_c"] = weather.temperature_c
        facts["relative_humidity"] = weather.relative_humidity
        facts["precipitation_mm"] = weather.precipitation_mm
        facts["precipitation"] = weather.precipitation_mm  # alias
        facts["precipitation_probability"] = weather.precipitation_probability
        facts["rain_mm"] = weather.rain_mm
        facts["showers_mm"] = weather.showers_mm
        facts["snowfall_mm"] = weather.snowfall_mm
        facts["wind_speed_kmh"] = weather.wind_speed_kmh
        facts["wind_gusts_kmh"] = weather.wind_gusts_kmh
        facts["uv_index"] = weather.uv_index
        facts["weather_code"] = weather.weather_code

        # Derived flags
        facts["is_thunderstorm"] = (weather.weather_code in THUNDERSTORM_CODES) if weather.weather_code else False
        facts["is_severe_weather"] = (weather.weather_code in SEVERE_WEATHER_CODES) if weather.weather_code else False
        facts["severe_weather_signal"] = _detect_severe(weather)

    # Intent facts
    facts["activity_category"] = intent.get("activity_category") or intent.get("activity")
    facts["user_group"] = intent.get("user_group")
    facts["outdoor_activity"] = True  # If the user is asking, it's outdoor

    return facts


def _detect_severe(weather: WeatherData) -> bool:
    """Detect severe weather based on generic thresholds — no hardcoded events."""
    if weather.weather_code and weather.weather_code in SEVERE_WEATHER_CODES:
        return True
    if weather.precipitation_mm is not None and weather.precipitation_mm >= 20:
        return True
    if weather.wind_gusts_kmh is not None and weather.wind_gusts_kmh >= 80:
        return True
    if weather.snowfall_mm is not None and weather.snowfall_mm >= 10:
        return True
    return False


def _evaluate_rule(
    rule: Union[SOPRule, SOPCondition], facts: dict[str, Any]
) -> bool:
    """Recursively evaluate an SOPRule or SOPCondition against facts."""
    if isinstance(rule, SOPCondition):
        actual = facts.get(rule.field)
        result = evaluate_condition(actual, rule.operator, rule.value)
        return result

    # SOPRule with all / any
    if rule.all is not None:
        return all(_evaluate_rule(sub, facts) for sub in rule.all)
    if rule.any is not None:
        return any(_evaluate_rule(sub, facts) for sub in rule.any)

    return False


def evaluate_sop(sop: SOP, weather: WeatherData, intent: dict[str, Any]) -> SOPMatch:
    """Evaluate a single SOP against weather facts and user intent."""
    facts = _build_facts(weather, intent)
    matched = _evaluate_rule(sop.applies_when, facts)
    reason = f"{'Matched' if matched else 'Did not match'} {sop.id} ({sop.name})"
    return SOPMatch(sop=sop, matched=matched, reason=reason)


def evaluate_all_sops(
    sops: list[SOP], weather: WeatherData, intent: dict[str, Any]
) -> list[SOPMatch]:
    """Evaluate every SOP and return all matches."""
    results: list[SOPMatch] = []
    for sop in sops:
        match = evaluate_sop(sop, weather, intent)
        if match.matched:
            results.append(match)
    return results


def resolve_conflicts(matches: list[SOPMatch]) -> SOPMatch | None:
    """Deterministic conflict resolution.

    1. Highest severity wins (critical > high > moderate > low).
    2. On tie, highest priority number wins.
    3. On tie, first in list wins.
    """
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    def _sort_key(m: SOPMatch):
        sev = SEVERITY_ORDER.get(m.sop.severity.lower(), 0)
        return (sev, m.sop.priority)

    sorted_matches = sorted(matches, key=_sort_key, reverse=True)
    winner = sorted_matches[0]
    logger.info(
        "Conflict resolution: selected %s (severity=%s, priority=%d) from %d candidates",
        winner.sop.id, winner.sop.severity, winner.sop.priority, len(matches),
    )
    winner.reason = (
        f"Selected {winner.sop.id} — highest severity/priority among "
        f"{[m.sop.id for m in matches]}"
    )
    return winner
