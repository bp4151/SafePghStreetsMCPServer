# Quick Start Guide

## Installation

1. **Install dependencies** (using UV or pip):
   ```bash
   uv pip install -r pyproject.toml
   # or
   pip install fastmcp httpx gpxpy uvicorn
   ```

2. **Verify Python version**:
   ```bash
   python --version  # Must be 3.11 or higher
   ```

## Running the Server

### Local Development
```bash
python main.py
```

The server will start on `http://localhost:8000` and display available tools.

### With Custom Port
```bash
PORT=9000 python main.py
```

### With Custom Host
```bash
MCP_HOST=127.0.0.1 PORT=8000 python main.py
```

## Testing the Server

### Using the Test Script
The project includes `analyze_safety.py` for testing:

```bash
python analyze_safety.py
```

This will:
1. Connect to the running MCP server
2. Load the sample GPX file (`Home_Highland_Park_Fountain.gpx`)
3. Call `summarize_route_safety` with the GPX content
4. Print the safety analysis

### Manual Testing with cURL
```bash
# Get crash data
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_wprdc_crash_data",
      "arguments": {}
    }
  }'
```

## Understanding the Output

### Safety Summary Example
```
Route Safety Summary by Street (Bicycle Crashes 2004-2024):
- FIFTH AVENUE: 145 crashes, Safety Score: 3/10
- LIBERTY AVENUE: 98 crashes, Safety Score: 5/10
- PENN AVENUE: 67 crashes, Safety Score: 5/10
- MAIN STREET: 12 crashes, Safety Score: 9/10
```

**Interpretation:**
- Streets with more crashes have lower safety scores
- Score ranges from 1 (most dangerous) to 10 (safest)
- Use this to plan alternate routes or be extra cautious on dangerous streets

## Providing Your Own GPX File

### Format
The MCP server accepts GPX files in XML format. You can:

1. **Export from mapping apps**:
   - Google Maps → Share → Download as GPX
   - Strava → Export activity as GPX
   - Komoot → Export route as GPX
   - Any GPS device with GPX export

2. **Create a test file** (`test_route.gpx`):
   ```xml
   <?xml version="1.0"?>
   <gpx version="1.1">
     <trk>
       <name>My Safe Route</name>
       <trkseg>
         <trkpt lat="40.4406" lon="-79.9959"/>
         <trkpt lat="40.4407" lon="-79.9960"/>
         <trkpt lat="40.4408" lon="-79.9961"/>
       </trkseg>
     </trk>
   </gpx>
   ```

3. **Use the analyze_safety.py script**:
   ```python
   analyze_route_safety("path/to/your_route.gpx")
   ```

## Deployment to Fly.io

### Setup
```bash
# Install flyctl: https://fly.io/docs/getting-started/installing-flyctl/
flyctl auth login
flyctl launch  # Follow prompts, select Python runtime
```

### Deploy
```bash
flyctl deploy
```

### View Logs
```bash
flyctl logs
```

## Troubleshooting

### "Connection refused" Error
- Ensure the server is running: `python main.py`
- Check the port matches (default 8000)
- Try: `http://localhost:8000` (not 127.0.0.1)

### "No bicycle crash records found"
- The GPX route may be outside Allegheny County
- Try the sample route: `server/Home_Highland_Park_Fountain.gpx`
- Verify GPX has valid coordinates (lat: -90 to 90, lon: -180 to 180)

### "Failed to parse GPX content"
- Ensure GPX file is valid XML
- Check that coordinates are numeric
- Validate GPX format: https://www.topografix.com/gpx.asp

### API Timeout
- WPRDC API might be temporarily unavailable
- Cached data remains available during outages
- Wait a moment and retry

## API Data Refresh

Data is cached in memory during the server's lifetime. To refresh:
1. Stop the server: `Ctrl+C`
2. Start a new instance: `python main.py`

## Security Notes

- The server accepts GPX content via POST requests
- No sensitive data is transmitted to external services
- All processing is local
- Environment variables are used for configuration (not hardcoded)

## Next Steps

- Review `MCP_SERVER_GUIDE.md` for detailed API documentation
- Check `server/main.py` for implementation details
- Explore alternative safety metrics and scoring algorithms
- Integrate with your cycling app or navigation tool
