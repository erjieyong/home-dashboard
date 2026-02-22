from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from home_dashboard.bus_api import BusArrivalResponse, fetch_bus_arrivals
from home_dashboard.config import BusServiceConfig, Config, load_config
from home_dashboard.weather_api import WeatherInfo, fetch_weather

_SGT: timezone = timezone(timedelta(hours=8))
_TEMPLATE_DIR: Path = Path(__file__).parent / "templates"


def create_app(config: Config | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if config is None:
        config = load_config()

    app: FastAPI = FastAPI(title="Home Dashboard")
    templates: Jinja2Templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

    # Register custom Jinja2 filters
    def format_time(dt: datetime | None) -> str:
        """Format a datetime to HH:MM in SGT."""
        if dt is None:
            return "--:--"
        sgt_dt: datetime = dt.astimezone(_SGT)
        return sgt_dt.strftime("%H:%M")

    templates.env.filters["format_time"] = format_time

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, device: str = "auto") -> HTMLResponse:
        """Main dashboard page."""
        if device == "auto":
            user_agent: str = request.headers.get("User-Agent", "").lower()
            if "kindle" in user_agent or "silk" in user_agent:
                device = "kindle"
            else:
                device = "nest"

        # Fetch all bus services + weather in parallel
        bus_tasks: list[asyncio.Task[BusArrivalResponse]] = [
            asyncio.to_thread(
                fetch_bus_arrivals,
                api_key=config.lta_api_key,
                bus_stop_code=svc.stop_code,
                service_no=svc.service_no,
                base_url=config.lta_api_base_url,
            )
            for svc in config.bus_services
        ]

        results = await asyncio.gather(
            *bus_tasks,
            asyncio.to_thread(
                fetch_weather,
                area=config.weather_area,
                pm25_region=config.pm25_region,
            ),
        )

        bus_results: list[BusArrivalResponse] = list(results[:-1])
        weather_result: WeatherInfo = results[-1]

        # Pair each bus result with its config for display
        bus_sections: list[dict] = [
            {"config": svc, "result": result}
            for svc, result in zip(config.bus_services, bus_results)
        ]

        now_sgt: datetime = datetime.now(_SGT)

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "bus_sections": bus_sections,
                "weather": weather_result,
                "refresh_seconds": config.refresh_seconds,
                "device": device,
                "now": now_sgt,
            },
        )

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


def main() -> None:
    """Entry point for development server."""
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()
    config: Config = load_config()
    app: FastAPI = create_app(config)
    uvicorn.run(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
