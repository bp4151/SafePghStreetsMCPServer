# Quick Reference Guide

## New Functions

### `detect_format_from_filepath(filepath: str) -> str`
Detects file format from filepath extension.

```python
from server.converters import detect_format_from_filepath

# Returns "gpx"
format_type = detect_format_from_filepath("routes/my_route.gpx")

# Returns "fit"
format_type = detect_format_from_filepath("/home/user/activity.fit")

# Raises FormatError if file doesn't exist
# Raises FormatError if extension not recognized
```

### `parse_route_data(source, filepath, verbose) -> RouteData`
Unified parser for GPX and FIT formats with automatic detection.

## Usage Patterns

### Pattern 1: Parse GPX file via filepath parameter
```python
from server.converters import parse_route_data

route_data = parse_route_data(
    filepath="routes/cycling_route.gpx"
)
print(f"Loaded {len(route_data.points)} points")
```

### Pattern 2: Parse FIT file via filepath parameter
```python
route_data = parse_route_data(
    filepath="/home/user/activities/morning_ride.fit",
    verbose=True  # Enable detailed logging
)
bounds = route_data.get_bounds()
print(f"Route bounds: {bounds}")
```

### Pattern 3: Auto-detect filepath in source parameter
```python
# String that is a valid file path → treated as filepath
route_data = parse_route_data(
    source="routes/weekend_route.gpx"
)

# Works with both absolute and relative paths
route_data = parse_route_data(
    source="/absolute/path/to/route.fit"
)
```

### Pattern 4: Parse GPX content directly
```python
gpx_xml = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata><name>My Route</name></metadata>
  <trk><trkseg>
    <trkpt lat="40.42" lon="-79.93"/>
    <trkpt lat="40.43" lon="-79.92"/>
  </trkseg></trk>
</gpx>"""

route_data = parse_route_data(source=gpx_xml)
```

### Pattern 5: Parse FIT binary content
```python
# Read FIT file as binary
with open("activity.fit", "rb") as f:
    fit_bytes = f.read()

# Parse directly
route_data = parse_route_data(source=fit_bytes)
```

### Pattern 6: Filepath parameter takes precedence
```python
# When both provided, filepath parameter wins
route_data = parse_route_data(
    source="ignored_content_or_path.gpx",
    filepath="actual/route.fit"  # This one is used
)
```

### Pattern 7: With error handling
```python
from server.format_models import FormatError

try:
    route_data = parse_route_data(filepath="route.gpx")
except FormatError as e:
    print(f"Error: {e}")  # File not found, invalid format, etc.
except ValueError as e:
    print(f"Missing parameter: {e}")  # Neither source nor filepath provided
```

### Pattern 8: Verbose logging
```python
route_data = parse_route_data(
    filepath="routes/route.gpx",
    verbose=True
)
# Output includes:
# - File detection steps
# - Format detection results
# - Number of points extracted
# - Route bounds
```

## Integration with Tools

### In Tool Functions

```python
@mcp.tool()
def analyze_route(route_content: Union[str, bytes], verbose: bool = False) -> str:
    """Analyze a route (GPX or FIT format)."""
    try:
        # Parse using new unified function
        route_data = parse_route_data(source=route_content, verbose=verbose)
        
        # Use route_data for analysis
        bounds = route_data.get_bounds()
        point_count = len(route_data.points)
        
        return f"Analyzed route with {point_count} points in area {bounds}"
    except FormatError as e:
        return f"Failed to parse route: {e}"
```

```python
@mcp.tool()
def analyze_fit_file(fit_file_path: str, verbose: bool = False) -> str:
    """Analyze a FIT file from disk."""
    try:
        # Parse using filepath parameter
        route_data = parse_route_data(filepath=fit_file_path, verbose=verbose)
        
        # Use route_data for analysis
        return f"Analyzed FIT file: {route_data.name}"
    except FormatError as e:
        return f"Failed to parse FIT file: {e}"
```

## Error Cases

### File not found
```python
from server.format_models import FormatError

try:
    parse_route_data(filepath="/nonexistent/file.gpx")
except FormatError as e:
    print(e)  # "File not found: /nonexistent/file.gpx"
```

### Unsupported file extension
```python
try:
    parse_route_data(filepath="route.txt")
except FormatError as e:
    print(e)  # "Unrecognized file extension '.txt'..."
```

### Neither source nor filepath provided
```python
try:
    parse_route_data()
except ValueError as e:
    print(e)  # "Either 'source' or 'filepath' must be provided..."
```

### Invalid format
```python
try:
    parse_route_data(source="invalid data")
except FormatError as e:
    print(e)  # "String content does not contain a valid GPX XML signature..."
```

## Best Practices

1. **Use explicit filepath parameter when parsing files**
   ```python
   # Good - clear intent
   parse_route_data(filepath="route.gpx")
   ```

2. **Use source parameter for content from APIs**
   ```python
   # Good - expected for API responses
   route_data = parse_route_data(source=gpx_xml_from_api)
   ```

3. **Always handle FormatError and ValueError**
   ```python
   try:
       route_data = parse_route_data(...)
   except (FormatError, ValueError) as e:
       logger.error(f"Parsing failed: {e}")
       return error_response
   ```

4. **Use verbose=True during development/debugging**
   ```python
   # During development
   route_data = parse_route_data(source=data, verbose=True)
   
   # In production
   route_data = parse_route_data(source=data, verbose=False)
   ```

5. **Check route_data before using**
   ```python
   route_data = parse_route_data(filepath="route.gpx")
   if not route_data.points:
       logger.warning("Route has no points")
   ```

## Accessing Route Data

After parsing, use RouteData properties:

```python
route_data = parse_route_data(filepath="route.gpx")

# Get number of points
point_count = len(route_data.points)

# Get bounds
min_lat, max_lat, min_lon, max_lon = route_data.get_bounds()

# Access individual points
for point in route_data.points:
    print(f"Lat: {point.latitude}, Lon: {point.longitude}")
    if point.elevation:
        print(f"Elevation: {point.elevation}m")
    if point.timestamp:
        print(f"Time: {point.timestamp}")

# Get metadata
print(route_data.metadata)  # {'format': 'GPX', 'source': '...', 'point_count': N}
```

## Migration from Old Functions

### Old Code
```python
route_data = parse_any_format(gpx_content)
route_data = fit_file_to_route_data("route.fit")
```

### New Code
```python
# Direct content replacement
route_data = parse_route_data(source=gpx_content)

# Filepath replacement
route_data = parse_route_data(filepath="route.fit")
```

Both old and new functions work - choose based on preference.
