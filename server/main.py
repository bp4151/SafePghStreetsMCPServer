import os
import httpx
import signal
import asyncio
import sys
from typing import List, Dict, Any, Optional, Union
from fastmcp import FastMCP
import gpxpy

# https://docs.python.org/3/howto/logging-cookbook.html
import logging

# Import format conversion utilities
from server.converters import parse_any_format, _extract_bbox_from_route_data
from server.format_models import FormatError

def _setup_logging():
    """Configure logging with standard format."""
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(FORMAT))
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

logger = _setup_logging()

# Create an MCP server
mcp = FastMCP("SafePghStreets")

WPRDC_API_URL = "https://data.wprdc.org/api/3/action/datastore_search_sql"
CUMULATIVE_CRASH_RESOURCE_ID = "2c13021f-74a9-4289-a1e5-fe0472c89881"

# In-memory cache for crash data
_crash_data_cache: Optional[List[Dict[str, Any]]] = None


def _normalize_street_name(street: Optional[str]) -> str:
    """Normalize street name for consistent comparison."""
    return street.strip().upper() if street else ""


def _safe_get_coordinates(record: Dict[str, Any]) -> Optional[tuple]:
    """Extract and validate lat/lon from a record. Returns (lat, lon) or None."""
    try:
        lat = float(record.get("DEC_LAT"))
        lon = float(record.get("DEC_LONG"))
        return (lat, lon)
    except (TypeError, ValueError):
        return None


def _fetch_all_crash_data() -> List[Dict[str, Any]]:
    """
    Helper function to fetch bicycle crash data from WPRDC and cache it.
    """
    global _crash_data_cache
    if _crash_data_cache is not None:
        return _crash_data_cache

    # CKAN SQL query - pulling fields needed for both tools, filtered for bicycles
    query = f'SELECT "CRASH_YEAR", "STREET_NAME", "DEC_LAT", "DEC_LONG" FROM "{CUMULATIVE_CRASH_RESOURCE_ID}" WHERE "BICYCLE" = \'1\''

    with httpx.Client() as client:
        try:
            response = client.get(WPRDC_API_URL, params={"sql": query}, timeout=60.0)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                error_msg = f"Error from WPRDC API: {data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)

            records = data.get("result", {}).get("records", [])
            _crash_data_cache = records
            return _crash_data_cache

        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred in _fetch_all_crash_data: {e}", exc_info=True)
            raise Exception(f"HTTP error occurred: {e}")
        except Exception as e:
            logger.error(f"Error in _fetch_all_crash_data: {e}", exc_info=True)
            raise Exception(f"An error occurred while fetching data: {e}")


def _extract_streets_from_gpx(gpx_content: Union[str, bytes]) -> set:
    """
    Extract street names from GPX route point names and comments.
    
    Args:
        gpx_content: GPX XML content (string or bytes)
    
    Returns:
        Set of normalized street names found in GPX metadata
    """
    try:
        if isinstance(gpx_content, bytes):
            gpx_content = gpx_content.decode('utf-8')
        
        gpx = gpxpy.parse(gpx_content)
        route_streets = set()
        
        for route in gpx.routes:
            for point in route.points:
                text = ""
                if point.name:
                    text += point.name
                if point.comment:
                    text += " " + point.comment
                if point.description:
                    text += " " + point.description
                
                text_upper = text.upper()
                words = text_upper.split()
                for i, word in enumerate(words):
                    if word in ("ONTO", "ON"):
                        if i + 1 < len(words):
                            street_start = i + 1
                            street_name = " ".join(words[street_start:])
                            street_name = _normalize_street_name(street_name)
                            if street_name and len(street_name) > 0:
                                route_streets.add(street_name)
                                break
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    text = ""
                    if point.name:
                        text += point.name
                    if point.comment:
                        text += " " + point.comment
                    if point.description:
                        text += " " + point.description
                    
                    text_upper = text.upper()
                    words = text_upper.split()
                    for i, word in enumerate(words):
                        if word in ("ONTO", "ON"):
                            if i + 1 < len(words):
                                street_start = i + 1
                                street_name = " ".join(words[street_start:])
                                street_name = _normalize_street_name(street_name)
                                if street_name and len(street_name) > 0:
                                    route_streets.add(street_name)
                                    break
        
        return route_streets
    
    except Exception as e:
        logger.warning(f"Could not extract street names from GPX metadata: {e}")
        return set()


@mcp.tool()
def get_wprdc_crash_data() -> str:
    """
    Fetch all bicycle crash data for Allegheny County from the WPRDC API (cached).
    """
    try:
        records = _fetch_all_crash_data()

        if not records:
            return "No bicycle crash records found."

        # Format the output
        output = [f"Found {len(records)} bicycle crash records:"]
        for rec in records:
            crash_year = rec.get("CRASH_YEAR")
            street = rec.get("STREET_NAME")
            lat = rec.get("DEC_LAT")
            lon = rec.get("DEC_LONG")
            output.append(f"- Year: {crash_year}, Street: {street}, Lat: {lat}, Lon: {lon}")

        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error in get_wprdc_crash_data: {e}", exc_info=True)
        return str(e)


def _extract_streets_from_gpx(gpx_content: Union[str, bytes]) -> set:
    """
    Extract street names from GPX route point names and comments.
    
    Args:
        gpx_content: GPX XML content (string or bytes)
    
    Returns:
        Set of normalized street names found in GPX metadata
    """
    try:
        import gpxpy
        
        if isinstance(gpx_content, bytes):
            gpx_content = gpx_content.decode('utf-8')
        
        gpx = gpxpy.parse(gpx_content)
        route_streets = set()
        
        for route in gpx.routes:
            for point in route.points:
                text = ""
                if point.name:
                    text += point.name
                if point.comment:
                    text += " " + point.comment
                if point.description:
                    text += " " + point.description
                
                text_upper = text.upper()
                
                words = text_upper.split()
                for i, word in enumerate(words):
                    if word in ("ONTO", "ON"):
                        if i + 1 < len(words):
                            street_start = i + 1
                            street_name = " ".join(words[street_start:])
                            street_name = _normalize_street_name(street_name)
                            if street_name and len(street_name) > 0:
                                route_streets.add(street_name)
                                break
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    text = ""
                    if point.name:
                        text += point.name
                    if point.comment:
                        text += " " + point.comment
                    if point.description:
                        text += " " + point.description
                    
                    text_upper = text.upper()
                    words = text_upper.split()
                    for i, word in enumerate(words):
                        if word in ("ONTO", "ON"):
                            if i + 1 < len(words):
                                street_start = i + 1
                                street_name = " ".join(words[street_start:])
                                street_name = _normalize_street_name(street_name)
                                if street_name and len(street_name) > 0:
                                    route_streets.add(street_name)
                                    break
        
        return route_streets
    
    except Exception as e:
        logger.warning(f"Could not extract street names from GPX metadata: {e}")
        return set()


@mcp.tool()
def summarize_route_safety(route_content: Union[str, bytes], verbose: bool = False) -> str:
    """
    Analyze the safety of each street along a route (GPX format).
    Returns a summary for each street with a safety score (1-10).
    Only includes streets that are explicitly in the route.
    
    Args:
        route_content: Route data as XML string (GPX).
        verbose: If True, log detailed parsing information for debugging.
    """
    try:
        route_data = parse_any_format(route_content, verbose=verbose)
    except FormatError as e:
        error_msg = f"Failed to parse route content: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error parsing route data: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

    try:
        bbox = _extract_bbox_from_route_data(route_data)
    except FormatError as e:
        error_msg = f"Cannot extract route bounds: {e}"
        logger.error(error_msg)
        return error_msg
    
    min_lat, max_lat, min_lon, max_lon = bbox
    
    route_streets = _extract_streets_from_gpx(route_content)
    if verbose and route_streets:
        logger.debug(f"Extracted {len(route_streets)} streets from GPX: {route_streets}")

    try:
        all_records = _fetch_all_crash_data()
        street_crashes = {}
        
        for rec in all_records:
            coords = _safe_get_coordinates(rec)
            if coords:
                lat, lon = coords
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    street = _normalize_street_name(rec.get("STREET_NAME"))
                    if street:
                        if route_streets and street not in route_streets:
                            continue
                        street_crashes[street] = street_crashes.get(street, 0) + 1

        if not street_crashes:
            return "No bicycle crash history found for streets in the route. Safety Score: 10/10 for all segments."

        output = ["Route Safety Summary by Street (Bicycle Crashes 2004-2024):"]
        sorted_streets = sorted(street_crashes.items(), key=lambda x: x[1], reverse=True)

        for street, count in sorted_streets:
            score = max(1, 10 - (count // 2))
            output.append(f"- {street}: {count} crashes, Safety Score: {score}/10")

        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error in summarize_route_safety: {e}", exc_info=True)
        return f"An error occurred during safety analysis: {e}"


@mcp.tool()
def match_crashes_by_street_name(route_content: Union[str, bytes], limit: int = 50, verbose: bool = False) -> str:
    """
    Match WPRDC crash data with a route by street name (GPX format).
    This extracts street names from crash records within the route's bounding box,
    then matches all crashes on those streets within the same bounding box.
    
    Args:
        route_content: Route data as XML string (GPX).
        limit: Maximum number of crash records to return.
        verbose: If True, log detailed parsing information for debugging.
    """
    try:
        route_data = parse_any_format(route_content, verbose=verbose)
    except FormatError as e:
        error_msg = f"Failed to parse route content: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error parsing route data: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

    try:
        bbox = _extract_bbox_from_route_data(route_data)
    except FormatError as e:
        error_msg = f"Cannot extract route bounds: {e}"
        logger.error(error_msg)
        return error_msg

    min_lat, max_lat, min_lon, max_lon = bbox

    try:
        all_records = _fetch_all_crash_data()

        # Step 1: Extract street names from crashes in the bounding box
        route_streets = set()
        for rec in all_records:
            coords = _safe_get_coordinates(rec)
            if coords:
                lat, lon = coords
                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    street = _normalize_street_name(rec.get("STREET_NAME"))
                    if street:
                        route_streets.add(street)

        if not route_streets:
            return "No streets with crash history found in the route area."

        # Step 2: Match crashes on those streets, but only within the bounding box
        matched_records = []
        for rec in all_records:
            if len(matched_records) >= limit:
                break
            street = _normalize_street_name(rec.get("STREET_NAME"))
            if street in route_streets:
                coords = _safe_get_coordinates(rec)
                if coords:
                    lat, lon = coords
                    if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                        matched_records.append(rec)

        if not matched_records:
            return "No crash records found on the identified route streets."

        output = [f"Found {len(matched_records)} bicycle crash records on {len(route_streets)} streets from the route:"]
        output.append(f"\nStreets identified on route: {', '.join(sorted(route_streets))}")
        output.append(f"\nCrash records (by street name matching):")
        
        for rec in matched_records:
            year = rec.get("CRASH_YEAR")
            street = rec.get("STREET_NAME")
            lat = rec.get("DEC_LAT")
            lon = rec.get("DEC_LONG")
            output.append(f"- {year}: {street} ({lat}, {lon})")

        return "\n".join(output)
    except Exception as e:
        logger.error(f"Error in match_crashes_by_street_name: {e}", exc_info=True)
        return f"An error occurred: {e}"


@mcp.tool()
def health_check() -> str:
    """
    Health check endpoint for fly.io monitoring.
    """
    return "OK"


if __name__ == "__main__":
    # Get port from environment variable (fly.io sets PORT)
    port = int(os.getenv("PORT", "8000"))
    host = os.environ.get("MCP_HOST", "0.0.0.0")

    try:
        mcp.run(host=host, transport="http", port=port, path="/mcp")
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Graceful shutdown completed")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


