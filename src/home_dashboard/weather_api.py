from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

_FORECAST_2H_URL: str = "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast"
_FORECAST_24H_URL: str = "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast"
_PM25_URL: str = "https://api.data.gov.sg/v1/environment/pm25"


def _pm25_level(value: int) -> str:
    """Return air quality level label for a PM2.5 reading (1-hour)."""
    if value <= 55:
        return "Good"
    if value <= 150:
        return "Moderate"
    if value <= 250:
        return "Unhealthy"
    if value <= 350:
        return "Very Unhealthy"
    return "Hazardous"


def _pm25_css_class(value: int) -> str:
    """Return CSS class for PM2.5 level."""
    if value <= 55:
        return "aqi-good"
    if value <= 150:
        return "aqi-moderate"
    return "aqi-unhealthy"


@dataclass(frozen=True)
class WeatherInfo:
    """Weather and air quality data."""

    forecast: str
    temp_low: int
    temp_high: int
    humidity_low: int
    humidity_high: int
    pm25: int | None
    pm25_level: str
    pm25_css_class: str
    error: str | None = None


def fetch_weather(
    area: str,
    pm25_region: str,
    timeout_seconds: float = 10.0,
) -> WeatherInfo:
    """Fetch weather forecast, temperature, and PM2.5 from data.gov.sg."""
    forecast: str = ""
    temp_low: int = 0
    temp_high: int = 0
    humidity_low: int = 0
    humidity_high: int = 0
    pm25_value: int | None = None
    errors: list[str] = []

    # 2-hour forecast for specific area
    try:
        resp: httpx.Response = httpx.get(_FORECAST_2H_URL, timeout=timeout_seconds)
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        items: list[dict[str, Any]] = data.get("items", [])
        if items:
            forecasts: list[dict[str, Any]] = items[0].get("forecasts", [])
            for f in forecasts:
                if f.get("area", "").lower() == area.lower():
                    forecast = f.get("forecast", "")
                    break
    except Exception:
        errors.append("weather forecast")

    # 24-hour forecast for temp and humidity ranges
    try:
        resp = httpx.get(_FORECAST_24H_URL, timeout=timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if items:
            general: dict[str, Any] = items[0].get("general", {})
            temp: dict[str, Any] = general.get("temperature", {})
            temp_low = int(temp.get("low", 0))
            temp_high = int(temp.get("high", 0))
            humidity: dict[str, Any] = general.get("relative_humidity", {})
            humidity_low = int(humidity.get("low", 0))
            humidity_high = int(humidity.get("high", 0))
    except Exception:
        errors.append("temperature")

    # PM2.5 reading
    try:
        resp = httpx.get(_PM25_URL, timeout=timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if items:
            readings: dict[str, Any] = items[0].get("readings", {})
            hourly: dict[str, Any] = readings.get("pm25_one_hourly", {})
            raw_value: int | float | None = hourly.get(pm25_region)
            if raw_value is not None:
                pm25_value = int(raw_value)
    except Exception:
        errors.append("PM2.5")

    error: str | None = None
    if errors:
        error = f"Failed to fetch: {', '.join(errors)}"

    return WeatherInfo(
        forecast=forecast or "N/A",
        temp_low=temp_low,
        temp_high=temp_high,
        humidity_low=humidity_low,
        humidity_high=humidity_high,
        pm25=pm25_value,
        pm25_level=_pm25_level(pm25_value) if pm25_value is not None else "N/A",
        pm25_css_class=_pm25_css_class(pm25_value) if pm25_value is not None else "",
        error=error,
    )
