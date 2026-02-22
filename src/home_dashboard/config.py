from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    lta_api_key: str = field(
        default_factory=lambda: os.environ.get("LTA_API_KEY", "")
    )
    bus_stop_code: str = field(
        default_factory=lambda: os.environ.get("BUS_STOP_CODE", "65629")
    )
    bus_service_no: str = field(
        default_factory=lambda: os.environ.get("BUS_SERVICE_NO", "34")
    )
    bus_stop_name: str = field(
        default_factory=lambda: os.environ.get("BUS_STOP_NAME", "Samudera Stn Exit A")
    )
    weather_area: str = field(
        default_factory=lambda: os.environ.get("WEATHER_AREA", "Punggol")
    )
    pm25_region: str = field(
        default_factory=lambda: os.environ.get("PM25_REGION", "north")
    )
    refresh_seconds: int = field(
        default_factory=lambda: int(os.environ.get("REFRESH_SECONDS", "30"))
    )
    lta_api_base_url: str = field(
        default_factory=lambda: os.environ.get(
            "LTA_API_BASE_URL",
            "https://datamall2.mytransport.sg/ltaodataservice/v3",
        )
    )
    host: str = field(
        default_factory=lambda: os.environ.get("HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("PORT", "8080"))
    )


def load_config() -> Config:
    """Load and validate configuration."""
    try:
        config: Config = Config()
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid configuration: {e}") from e
    if not config.lta_api_key:
        raise ValueError("LTA_API_KEY environment variable is required")
    return config
