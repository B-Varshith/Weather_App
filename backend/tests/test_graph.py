"""Integration tests for the LangGraph with mocked services."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.weather import WeatherData, LocationData


def _mock_weather(**overrides) -> WeatherData:
    """Create a mock WeatherData object."""
    defaults = {
        "source": "test",
        "retrieved_at": "2024-01-01T12:00:00",
        "location": LocationData(name="Bhopal", latitude=23.2599, longitude=77.4126),
        "temperature_c": 32,
        "relative_humidity": 65,
        "wind_speed_kmh": 44,
        "wind_gusts_kmh": 55,
        "uv_index": 6,
        "precipitation_mm": 2,
        "precipitation_probability": 40,
        "rain_mm": 1,
        "showers_mm": 0,
        "snowfall_mm": 0,
        "weather_code": 3,
    }
    defaults.update(overrides)
    return WeatherData(**defaults)


class TestSopRepository:
    def test_load_sops(self):
        """SOP repository should load all SOPs from YAML."""
        from app.repositories.sop_repository import SOPRepository
        repo = SOPRepository()
        sops = repo.load()
        assert len(sops) >= 10  # At least 10 required
        assert len(sops) == 12  # We defined 12

    def test_sop_categories(self):
        """SOPs should cover at least 3 categories."""
        from app.repositories.sop_repository import SOPRepository
        repo = SOPRepository()
        sops = repo.load()
        categories = set(s.category for s in sops)
        assert len(categories) >= 3

    def test_sop_severities(self):
        """SOPs should have multiple severity levels."""
        from app.repositories.sop_repository import SOPRepository
        repo = SOPRepository()
        sops = repo.load()
        severities = set(s.severity for s in sops)
        assert len(severities) >= 2

    def test_get_by_id(self):
        """Should retrieve a specific SOP by ID."""
        from app.repositories.sop_repository import SOPRepository
        repo = SOPRepository()
        repo.load()
        sop = repo.get_by_id("SOP-002")
        assert sop is not None
        assert sop.name == "High Wind for Cycling"


class TestGraphIntegration:
    """Test that the SOP evaluation with mocked weather data works end-to-end."""

    def test_cycling_high_wind(self):
        """High wind + cycling should match SOP-002."""
        from app.services.sop_engine import evaluate_all_sops, resolve_conflicts
        from app.repositories.sop_repository import SOPRepository

        weather = _mock_weather(wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)
        matched_ids = [m.sop.id for m in matches]

        assert "SOP-002" in matched_ids

        winner = resolve_conflicts(matches)
        assert winner is not None
        assert winner.sop.id == "SOP-002"

    def test_thunderstorm(self):
        """Thunderstorm weather code should trigger SOP-010."""
        from app.services.sop_engine import evaluate_all_sops
        from app.repositories.sop_repository import SOPRepository

        weather = _mock_weather(weather_code=95)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)
        matched_ids = [m.sop.id for m in matches]

        assert "SOP-010" in matched_ids

    def test_severe_weather_override(self):
        """Extreme precipitation should trigger SOP-012 (critical)."""
        from app.services.sop_engine import evaluate_all_sops, resolve_conflicts
        from app.repositories.sop_repository import SOPRepository

        weather = _mock_weather(precipitation_mm=25, wind_speed_kmh=45)
        intent = {"activity_category": "cycling"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)
        matched_ids = [m.sop.id for m in matches]

        assert "SOP-012" in matched_ids

        winner = resolve_conflicts(matches)
        # Critical severity should win
        assert winner.sop.severity == "critical"

    def test_no_match(self):
        """Photography (no SOP) should return no matches."""
        from app.services.sop_engine import evaluate_all_sops
        from app.repositories.sop_repository import SOPRepository

        weather = _mock_weather(wind_speed_kmh=10, uv_index=3, temperature_c=25)
        intent = {"activity_category": "photography"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)

        # Photography has no SOP, and weather is mild
        matched_ids = [m.sop.id for m in matches]
        # Only generic SOPs might match if thresholds are crossed
        # With mild weather, nothing should match
        assert len(matches) == 0

    def test_picnic_fuzzy(self):
        """Picnic with bad conditions should trigger SOP-011."""
        from app.services.sop_engine import evaluate_all_sops
        from app.repositories.sop_repository import SOPRepository

        weather = _mock_weather(precipitation_probability=75, precipitation_mm=3, wind_speed_kmh=20)
        intent = {"activity_category": "picnic"}

        sops = SOPRepository().get_all()
        matches = evaluate_all_sops(sops, weather, intent)
        matched_ids = [m.sop.id for m in matches]

        assert "SOP-011" in matched_ids
