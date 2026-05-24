# SafePghStreets MCP Server

An MCP (Model Context Protocol) server that analyzes bicycle crash safety on Pittsburgh streets using GPS routes (GPX format) and WPRDC Allegheny County Crash data.

## Overview

This server provides tools for cyclists to understand the safety profile of their planned routes by:
1. Querying bicycle crash data from the WPRDC (Western Pennsylvania Regional Data Center)
2. Matching crash records to streets in your GPS route (GPX format)
3. Generating safety summaries with 1-10 safety scores for each street

## Supported Formats

The server processes GPX route format:

### GPX (GPS Exchange Format)
- **Type**: XML-based text format
- **Common Source**: Most cycling apps, Strava, Garmin, Wahoo, etc.
- **Extension**: `.gpx`
- **Input**: XML string content
- **Use Case**: Web apps, standard route formats, direct API responses

## Architecture

- **main.py**: Root entry point that starts the HTTP MCP server
- **server/main.py**: Core implementation with all MCP tools and logic
- **server/format_models.py**: Common data structures (RouteData, TrackPoint)
- **server/converters/**: Format converters
  - `gpx_converter.py`: GPX → RouteData
  - `__init__.py`: Format detection and route data parsing

## Available Tools

### 1. `get_wprdc_crash_data()`
Fetches all bicycle crash records from WPRDC for Allegheny County (2004-2024).

**Returns:**
- List of crash records with year, street name, and coordinates
- Data is cached in memory after first fetch

### 2. `match_crashes_from_gpx(gpx_content, limit=50)`
Matches bicycle crashes within a GPX route's bounding box.

**Parameters:**
- `gpx_content` (str): XML content of the GPX file
- `limit` (int): Maximum number of records to return (default: 50)

**Returns:**
- Crash records found within the geographic area of the route

### 2. `match_crashes_by_street_name(route_content, limit=50, verbose=False)`
Matches crashes by extracting street names from the route's area, then finding all crashes on those streets.

**Parameters:**
- `route_content` (str or bytes): Route data as GPX XML string or FIT binary bytes
- `limit` (int): Maximum number of records to return (default: 50)
- `verbose` (bool): Enable detailed parsing logs (default: False)

**Returns:**
- List of streets identified in the route area
- All crash records on those streets

### 3. `summarize_route_safety(route_content, verbose=False)`
Generates a safety summary for each street along the route with 1-10 safety scores.

**Parameters:**
- `route_content` (str or bytes): Route data as GPX XML string or FIT binary bytes
- `verbose` (bool): Enable detailed parsing logs (default: False)

**Returns:**
- Safety analysis by street:
  - Number of bicycle crashes per street
  - Safety score (1-10): 10 = safest (no crashes), 1 = least safe (most crashes)
  - Streets sorted by danger level (most crashes first)

### 4. `health_check()`
Simple health check endpoint for monitoring (returns "OK").

## Safety Score Calculation

The safety score is calculated as: `max(1, 10 - (crash_count // 2))`

- **Score 10**: No bicycle crash history on the street
- **Score 9**: 1-2 crashes
- **Score 8**: 3-4 crashes
- **Score 7**: 5-6 crashes
- ...
- **Score 1**: 18+ crashes

**Note:** This is a simplified heuristic. A production system would normalize by street length, traffic volume, and other factors.

## Configuration

The server reads from environment variables:
- `PORT`: Server port (default: 8000)
- `MCP_HOST`: Server host (default: 0.0.0.0)

### For Fly.io Deployment

Set the `PORT` environment variable via fly.toml:
```toml
[env]
PORT = "8000"
```

## Data Source

- **API**: WPRDC (Western Pennsylvania Regional Data Center)
- **Resource**: Allegheny County Crash Data
- **Resource ID**: `2c13021f-74a9-4289-a1e5-fe0472c89881`
- **Query**: Filters for records where BICYCLE = '1'
- **Time Period**: 2004-2024
- **Update Frequency**: Cached per server session

## Example Usage

### Start the Server
```bash
python main.py
```

The server will start on `http://localhost:8000`

### Via HTTP MCP Client - GPX Format
```python
import httpx

# Send GPX content to analyze route safety
gpx_content = """<?xml version="1.0"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="40.4406" lon="-79.9959">
        <ele>240</ele>
      </trkpt>
      <trkpt lat="40.4407" lon="-79.9960">
        <ele>242</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>"""

client = httpx.Client()
response = client.post(
    "http://localhost:8000/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "summarize_route_safety",
            "arguments": {"route_content": gpx_content, "verbose": False}
        }
    }
)
print(response.json())
```

### Via HTTP MCP Client - FIT Format
```python
import httpx

# Send FIT file binary to analyze route safety
with open("route.fit", "rb") as f:
    fit_content = f.read()

client = httpx.Client()
response = client.post(
    "http://localhost:8000/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "summarize_route_safety",
            "arguments": {
                "route_content": fit_content.decode('latin-1'),  # Binary as string for JSON
                "verbose": True  # Enable detailed logging
            }
        }
    }
)
print(response.json())
```

**Note:** For FIT files via JSON, you may need to encode binary as base64 or latin-1 depending on your client implementation.

## Dependencies

- `fastmcp`: MCP server framework
- `httpx`: HTTP client for API requests
- `gpxpy`: GPX file parsing (XML-based routes)
- `fitparse`: FIT file parsing (Garmin binary format)
- `uvicorn`: ASGI server
- `python >= 3.11`

### Installing Dependencies
```bash
pip install -r requirements.txt
# or
python -m pip install fastmcp httpx gpxpy fitparse uvicorn
```

## Error Handling

The server includes comprehensive error handling with strict validation:
- Invalid GPX XML files
- Corrupted FIT binary files
- Invalid or out-of-range coordinates (lat: -90 to 90, lon: -180 to 180)
- Missing track points in routes
- Format detection failures
- API connection failures
- Data parsing errors

**Debugging:** Use `verbose=True` parameter in tools to enable detailed logging for troubleshooting format or parsing issues.

All errors are logged and returned as user-friendly error messages.

## Performance Considerations

1. **Caching**: Crash data is cached in memory after first fetch to avoid repeated API calls
2. **Bounding Box Filtering**: Geographic filtering is done locally after data fetch
3. **Street Name Matching**: Case-insensitive, whitespace-normalized matching
4. **Limits**: Default limit of 50 records per query to prevent overwhelming responses

## Future Improvements

- Normalize safety scores by street length and traffic volume
- Add temporal analysis (crashes by season/month)
- Integrate with bicycle infrastructure data
- Support for additional route formats (KML, GeoJSON, TCX)
- Real-time data updates via webhooks
- User-configurable safety score algorithms
- Format conversion utilities (export routes to different formats)
- Elevation profile analysis and hill difficulty scoring
- Route optimization for safest path
