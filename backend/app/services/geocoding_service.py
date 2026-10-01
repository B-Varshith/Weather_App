"""Geocoding service — resolves city names to lat/lon via Open-Meteo."""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import settings
from app.models.weather import LocationData

logger = logging.getLogger(__name__)


class LocationResolutionError(Exception):
    """Raised when a location cannot be resolved."""
    pass


class GeocodingService:
    """Production geocoding implementation backed by Open-Meteo."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.GEOCODING_BASE_URL

    async def resolve(self, city: str) -> LocationData:
        """Resolve a city name to coordinates.

        Raises LocationResolutionError when the city cannot be found.
        """
        if not city or not city.strip():
            raise LocationResolutionError("No city name provided")

        params = {"name": city.strip(), "count": 1, "language": "en", "format": "json"}

        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT) as client:
                resp = await client.get(self.base_url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.error("Geocoding API error for %s: %s", city, exc)
            raise LocationResolutionError(
                f"Geocoding API request failed for '{city}'"
            ) from exc

        results = data.get("results")
        if not results:
            logger.warning("No geocoding results for %s", city)
            raise LocationResolutionError(
                f"Could not resolve location '{city}'"
            )

        top = results[0]
        location = LocationData(
            name=top.get("name", city),
            latitude=top["latitude"],
            longitude=top["longitude"],
            country=top.get("country"),
        )
        logger.info("Resolved %s → %s (%.4f, %.4f)", city, location.name,
                     location.latitude, location.longitude)
        return location
