"""Location service — thin wrapper combining geocoding with caching."""

from __future__ import annotations

import logging
from typing import Optional

from app.models.weather import LocationData
from app.services.geocoding_service import GeocodingService, LocationResolutionError

logger = logging.getLogger(__name__)

# Simple in-memory geocoding cache (city → LocationData)
_cache: dict[str, LocationData] = {}


class LocationService:
    """Caches geocoding results for the lifetime of the process."""

    def __init__(self, geocoding_service: Optional[GeocodingService] = None):
        self.geo = geocoding_service or GeocodingService()

    async def resolve(self, city: str) -> LocationData:
        """Resolve a city name, returning cached data when available."""
        key = city.strip().lower()
        if key in _cache:
            logger.info("Geocoding cache hit for '%s'", city)
            return _cache[key]

        location = await self.geo.resolve(city)
        _cache[key] = location
        return location
