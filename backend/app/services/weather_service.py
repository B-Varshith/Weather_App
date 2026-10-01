"""Weather service — fetches live weather from Open-Meteo."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import settings
from app.models.weather import LocationData, WeatherData

logger = logging.getLogger(__name__)


class WeatherFetchError(Exception):
    """Raised when weather data cannot be retrieved."""
    pass


# Fields we request from Open-Meteo (hourly)
HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "rain",
    "showers",
    "snowfall",
    "wind_speed_10m",
    "wind_gusts_10m",
    "uv_index",
    "weather_code",
]


class WeatherService:
    """Production weather provider backed by Open-Meteo."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.WEATHER_BASE_URL

    async def get_weather(
        self, latitude: float, longitude: float, location: LocationData
    ) -> WeatherData:
        """Fetch current/hourly weather for the given coordinates.

        Raises WeatherFetchError on any failure.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(HOURLY_FIELDS),
            "forecast_days": 1,
            "timezone": "auto",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.API_TIMEOUT) as client:
                resp = await client.get(self.base_url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            logger.error("Weather API error: %s", exc)
            raise WeatherFetchError(
                f"Weather API request failed for ({latitude}, {longitude})"
            ) from exc

        # Pick the closest hour to "now" (or the latest available)
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
        idx = 0
        for i, t in enumerate(times):
            if t <= now_str:
                idx = i

        def _val(key: str, default=None):
            arr = hourly.get(key, [])
            return arr[idx] if idx < len(arr) else default

        weather = WeatherData(
            source="open-meteo",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            location=location,
            temperature_c=_val("temperature_2m"),
            relative_humidity=_val("relative_humidity_2m"),
            precipitation_mm=_val("precipitation"),
            precipitation_probability=_val("precipitation_probability"),
            rain_mm=_val("rain"),
            showers_mm=_val("showers"),
            snowfall_mm=_val("snowfall"),
            wind_speed_kmh=_val("wind_speed_10m"),
            wind_gusts_kmh=_val("wind_gusts_10m"),
            uv_index=_val("uv_index"),
            weather_code=_val("weather_code"),
        )

        logger.info(
            "Weather fetched for %s: temp=%.1f wind=%.1f precip_prob=%s uv=%s code=%s",
            location.name,
            weather.temperature_c or 0,
            weather.wind_speed_kmh or 0,
            weather.precipitation_probability,
            weather.uv_index,
            weather.weather_code,
        )
        return weather
