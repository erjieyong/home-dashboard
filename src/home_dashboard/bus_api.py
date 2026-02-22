from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx


class BusLoad(Enum):
    """Bus passenger load levels."""

    SEATS_AVAILABLE = "SEA"
    STANDING_AVAILABLE = "SDA"
    LIMITED_STANDING = "LSD"
    UNKNOWN = ""

    @property
    def display_text(self) -> str:
        mapping: dict[str, str] = {
            "SEA": "Seats Avail",
            "SDA": "Standing",
            "LSD": "Full",
            "": "Unknown",
        }
        return mapping.get(self.value, "Unknown")

    @property
    def css_class(self) -> str:
        mapping: dict[str, str] = {
            "SEA": "load-seats",
            "SDA": "load-standing",
            "LSD": "load-full",
            "": "load-unknown",
        }
        return mapping.get(self.value, "load-unknown")


class BusType(Enum):
    """Bus vehicle types."""

    SINGLE_DECK = "SD"
    DOUBLE_DECK = "DD"
    BENDY = "BD"
    UNKNOWN = ""

    @property
    def display_text(self) -> str:
        mapping: dict[str, str] = {
            "SD": "Single",
            "DD": "Double",
            "BD": "Bendy",
            "": "?",
        }
        return mapping.get(self.value, "?")


@dataclass(frozen=True)
class BusArrival:
    """A single bus arrival entry."""

    estimated_arrival: datetime | None
    minutes_away: int | None
    load: BusLoad
    bus_type: BusType
    is_wheelchair_accessible: bool
    is_arriving: bool
    has_data: bool


@dataclass(frozen=True)
class BusArrivalResponse:
    """Complete bus arrival response for a service."""

    bus_stop_code: str
    service_no: str
    arrivals: list[BusArrival]
    fetched_at: datetime
    error: str | None = None


def _parse_arrival(bus_data: dict[str, Any], now: datetime) -> BusArrival:
    """Parse a single NextBus/NextBus2/NextBus3 entry."""
    estimated_str: str = bus_data.get("EstimatedArrival", "")

    if not estimated_str:
        return BusArrival(
            estimated_arrival=None,
            minutes_away=None,
            load=BusLoad.UNKNOWN,
            bus_type=BusType.UNKNOWN,
            is_wheelchair_accessible=False,
            is_arriving=False,
            has_data=False,
        )

    estimated: datetime = datetime.fromisoformat(estimated_str)
    if estimated.tzinfo is None:
        estimated = estimated.replace(tzinfo=timezone.utc)

    delta_seconds: float = (estimated - now).total_seconds()
    minutes: int = max(0, int(delta_seconds // 60))

    load_str: str = bus_data.get("Load", "")
    try:
        load: BusLoad = BusLoad(load_str)
    except ValueError:
        load = BusLoad.UNKNOWN

    type_str: str = bus_data.get("Type", "")
    try:
        bus_type: BusType = BusType(type_str)
    except ValueError:
        bus_type = BusType.UNKNOWN

    feature: str = bus_data.get("Feature", "")

    return BusArrival(
        estimated_arrival=estimated,
        minutes_away=minutes,
        load=load,
        bus_type=bus_type,
        is_wheelchair_accessible=feature == "WAB",
        is_arriving=minutes <= 1,
        has_data=True,
    )


def fetch_bus_arrivals(
    api_key: str,
    bus_stop_code: str,
    service_no: str,
    base_url: str,
    timeout_seconds: float = 10.0,
) -> BusArrivalResponse:
    """Fetch bus arrival times from LTA DataMall API."""
    now: datetime = datetime.now(timezone.utc)
    url: str = f"{base_url}/BusArrival"
    params: dict[str, str] = {
        "BusStopCode": bus_stop_code,
        "ServiceNo": service_no,
    }
    headers: dict[str, str] = {
        "AccountKey": api_key,
        "accept": "application/json",
    }

    try:
        response: httpx.Response = httpx.get(
            url, params=params, headers=headers, timeout=timeout_seconds
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except httpx.TimeoutException:
        return BusArrivalResponse(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            arrivals=[],
            fetched_at=now,
            error="API request timed out",
        )
    except httpx.HTTPStatusError as exc:
        return BusArrivalResponse(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            arrivals=[],
            fetched_at=now,
            error=f"API returned HTTP {exc.response.status_code}",
        )
    except httpx.RequestError:
        return BusArrivalResponse(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            arrivals=[],
            fetched_at=now,
            error="Network error",
        )
    except Exception:
        return BusArrivalResponse(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            arrivals=[],
            fetched_at=now,
            error="Unexpected error",
        )

    services: list[dict[str, Any]] = data.get("Services", [])
    if not services:
        return BusArrivalResponse(
            bus_stop_code=bus_stop_code,
            service_no=service_no,
            arrivals=[],
            fetched_at=now,
            error="No service data. Bus may not be operating.",
        )

    service: dict[str, Any] = services[0]
    arrivals: list[BusArrival] = []
    for key in ("NextBus", "NextBus2", "NextBus3"):
        bus_data: dict[str, Any] = service.get(key, {})
        if bus_data:
            arrival: BusArrival = _parse_arrival(bus_data, now)
            if arrival.has_data:
                arrivals.append(arrival)

    return BusArrivalResponse(
        bus_stop_code=bus_stop_code,
        service_no=service_no,
        arrivals=arrivals,
        fetched_at=now,
    )
