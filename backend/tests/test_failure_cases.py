"""Tests for failure scenarios — location and weather failures."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.geocoding_service import GeocodingService, LocationResolutionError
from app.services.weather_service import WeatherService, WeatherFetchError


@pytest.mark.asyncio
async def test_unknown_location():
    """Geocoding service should raise LocationResolutionError for unknown cities."""
    mock_response = {"results": None}

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_resp.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        svc = GeocodingService()
        with pytest.raises(LocationResolutionError):
            await svc.resolve("XYZ_UNKNOWN_CITY_12345")


@pytest.mark.asyncio
async def test_empty_location():
    """Empty location should raise LocationResolutionError."""
    svc = GeocodingService()
    with pytest.raises(LocationResolutionError):
        await svc.resolve("")


@pytest.mark.asyncio
async def test_weather_api_timeout():
    """Weather service should raise WeatherFetchError on timeout."""
    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        from app.models.weather import LocationData
        loc = LocationData(name="Test", latitude=0, longitude=0)
        svc = WeatherService()
        with pytest.raises(WeatherFetchError):
            await svc.get_weather(0, 0, loc)
