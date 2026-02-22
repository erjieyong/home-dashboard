# Home Dashboard

A lightweight home dashboard website designed for Google Nest Hub 1 and Kindle 2019. Server-side rendered with auto-refresh — no JavaScript required.

## Features

- **Bus arrival times** for multiple services — Bus 34 (Samudera Stn Exit A) and Bus 104 (Blk 413C) by default (LTA DataMall API)
- **Weather forecast** for Punggol with temperature and humidity ranges (data.gov.sg)
- **PM2.5 air quality index** for the north region (data.gov.sg)
- **Current date and time** in SGT
- Auto-refreshes every 30 seconds via `<meta http-equiv="refresh">`
- Device-adaptive layout: dark theme for Nest Hub, high-contrast grayscale for Kindle

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- LTA DataMall API key ([register here](https://datamall.lta.gov.sg/content/datamall/en/request-for-api.html))

## Setup

```bash
# Install dependencies
uv sync

# Create .env from template and add your API key
cp .env.example .env
# Edit .env and set LTA_API_KEY

# Run the dashboard
uv run home-dashboard
```

The dashboard will be available at `http://localhost:8080/`.

## Usage

| URL | Description |
|-----|-------------|
| `http://<ip>:8080/` | Auto-detect device (Kindle detected via User-Agent) |
| `http://<ip>:8080/?device=nest` | Force Nest Hub layout (dark, horizontal) |
| `http://<ip>:8080/?device=kindle` | Force Kindle layout (white, vertical) |
| `http://<ip>:8080/health` | Health check endpoint |

## Configuration

All configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LTA_API_KEY` | *(required)* | LTA DataMall API key |
| `BUS_SERVICES` | *(see below)* | JSON array of bus services to track |
| `WEATHER_AREA` | `Punggol` | Area for 2-hour weather forecast |
| `PM25_REGION` | `north` | Region for PM2.5 reading (north/south/east/west/central) |
| `REFRESH_SECONDS` | `30` | Page auto-refresh interval in seconds |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8080` | Server port |

`BUS_SERVICES` defaults to:

```json
[
  {"stop_code": "65629", "service_no": "34", "stop_name": "Samudera Stn Exit A"},
  {"stop_code": "65651", "service_no": "104", "stop_name": "Blk 413C"}
]
```

## Docker

```bash
# Build the image
docker build --platform linux/amd64 -t erjieyong/home-dashboard:latest -t erjieyong/home-dashboard:0.1.0 .

# docker push the image
docker push erjieyong/home-dashboard:latest && docker push erjieyong/home-dashboard:0.1.0

# Run with environment variables
docker run -d -p 8080:8080 \
  -e LTA_API_KEY=your_api_key_here \
  home-dashboard
```

Or with an `.env` file:

```bash
docker run -d -p 8080:8080 --env-file .env home-dashboard
```

## APIs Used

- [LTA DataMall Bus Arrival v3](https://datamall.lta.gov.sg/content/datamall/en/dynamic-data.html) — real-time bus arrival times
- [data.gov.sg 2-Hour Weather Forecast](https://data.gov.sg/datasets/d_2de96ee53ef9075c85e34ade4ec16dca/view) — area-level weather forecast
- [data.gov.sg 24-Hour Weather Forecast](https://data.gov.sg/datasets/d_1efe4c3aaf37d404485e55f55a1c0a58/view) — temperature and humidity ranges
- [data.gov.sg PM2.5](https://data.gov.sg/datasets/d_8c9f093c5e15e204c3a1dc1a29b28644/view) — hourly PM2.5 readings by region
