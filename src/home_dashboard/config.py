from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

_DEFAULT_BUS_SERVICES: str = json.dumps([
    {"stop_code": "65629", "service_no": "34", "stop_name": "Samudera Stn Exit A"},
    {"stop_code": "65651", "service_no": "104", "stop_name": "Blk 413C"},
])


@dataclass(frozen=True)
class BusServiceConfig:
    """Configuration for a single bus service to track."""

    stop_code: str
    service_no: str
    stop_name: str


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    lta_api_key: str = field(
        default_factory=lambda: os.environ.get("LTA_API_KEY", "")
    )
    bus_services: tuple[BusServiceConfig, ...] = field(
        default_factory=lambda: tuple(
            BusServiceConfig(**svc)
            for svc in json.loads(os.environ.get("BUS_SERVICES", _DEFAULT_BUS_SERVICES))
        )
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
    if not config.bus_services:
        raise ValueError("BUS_SERVICES must contain at least one service")
    return config
