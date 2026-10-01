"""Unit tests for the weather service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.weather_service import WeatherService, WeatherFetchError
from app.models.weather import LocationData


@pytest.fixture
def location():
    return LocationData(name="Bhopal", latitude=23.2599, longitude=77.4126)


@pytest.fixture
def weather_service():
    return WeatherService()


@pytest.mark.asyncio
async def test_weather_fetch_success(weather_service, location):
    """Weather service should return structured data on success."""
    mock_response = {
        "hourly": {
            "time": ["2024-01-01T12:00"],
            "temperature_2m": [32.5],
            "relative_humidity_2m": [65],
            "precipitation": [2.1],
            "precipitation_probability": [55],
            "rain": [1.5],
            "showers": [0.6],
            "snowfall": [0],
            "wind_speed_10m": [22.3],
            "wind_gusts_10m": [35.1],
            "uv_index": [6.2],
            "weather_code": [3],
        }
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        weather = await weather_service.get_weather(23.2599, 77.4126, location)

        assert weather.source == "open-meteo"
        assert weather.temperature_c == 32.5
        assert weather.wind_speed_kmh == 22.3
        assert weather.precipitation_probability == 55
        assert weather.uv_index == 6.2


@pytest.mark.asyncio
async def test_weather_fetch_failure(weather_service, location):
    """Weather service should raise WeatherFetchError on API failure."""
    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        with pytest.raises(WeatherFetchError):
            await weather_service.get_weather(23.2599, 77.4126, location)
