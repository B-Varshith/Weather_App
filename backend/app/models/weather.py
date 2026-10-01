"""Pydantic models for weather data."""

from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class LocationData(BaseModel):
    """Resolved location from geocoding."""
    name: str
    latitude: float
    longitude: float
    country: Optional[str] = None


class WeatherData(BaseModel):
    """Normalised weather snapshot used by the SOP engine."""
    source: str = "open-meteo"
    retrieved_at: str = ""
    location: LocationData

    temperature_c: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation_mm: Optional[float] = None
    precipitation_probability: Optional[float] = None
    rain_mm: Optional[float] = None
    showers_mm: Optional[float] = None
    snowfall_mm: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    wind_gusts_kmh: Optional[float] = None
    uv_index: Optional[float] = None
    weather_code: Optional[int] = None
