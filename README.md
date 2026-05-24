# SafePghStreets MCP Server

An MCP (Model Context Protocol) server that analyzes bicycle crash safety on Pittsburgh streets using GPS routes (GPX/FIT format) and [WPRDC](https://data.wprdc.org) Allegheny County crash data.

## Features

- **`get_wprdc_crash_data`** — Fetch all bicycle crash records for Allegheny County (2004–2024)
- **`summarize_route_safety`** — Score each street on a GPX/FIT route from 1 (dangerous) to 10 (safe) based on historical crash counts
- **`match_crashes_by_street_name`** — Match crash records to streets within a route's bounding box
- **`health_check`** — Simple monitoring endpoint

## Quick Start

```bash
pip install fastmcp httpx gpxpy fitparse uvicorn
python server/main.py
```

Server starts on `http://0.0.0.0:8000` (endpoint `/mcp`).

Requires Python 3.11+.

### Docker

```bash
docker-compose up --build
```

## Documentation

| File | Description |
|------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Install, run, test, and deploy instructions |
| [MCP_SERVER_GUIDE.md](MCP_SERVER_GUIDE.md) | Detailed API reference, safety score formula, JSON-RPC examples |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Code examples for `parse_route_data()` and format detection |
| [AGENT.md](AGENT.md) | Workflow for combined DOMI obstruction + safety assessment |
| [INDEX.md](INDEX.md) | Full documentation index for the format detection system |

## Data Source

- **API**: [WPRDC Allegheny County Crash Data](https://data.wprdc.org/dataset/allegheny-county-crash-data)
- **Filter**: Bicycle-involved crashes (`BICYCLE = '1'`)
- **Caching**: Fetched once per server session and cached in memory

## License

MIT — see [LICENSE.md](LICENSE.md).
