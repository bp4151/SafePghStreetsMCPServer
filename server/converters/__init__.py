"""
Format detection and conversion orchestration.

Handles automatic format detection and converts GPX/FIT files to common RouteData format.
"""

import logging
from typing import Union

from server.format_models import RouteData, FormatError
from server.converters.gpx_converter import gpx_to_route_data

logger = logging.getLogger(__name__)


def detect_format(content: Union[str, bytes]) -> str:
    """
    Detect the format of route data.

    Detection order:
    1. bytes → check for GPX (XML start) → "gpx"
    2. str → check for GPX XML (<?xml or <gpx) → "gpx"

    Args:
        content: string (GPX XML)

    Returns:
        "gpx"

    Raises:
        FormatError: If format cannot be determined
    """
    try:
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise FormatError("Binary content detected; only text-based GPX format is supported")

        if isinstance(content, str):
            content_stripped = content.strip()

            if content_stripped.startswith('<?xml') or content_stripped.startswith('<gpx'):
                return "gpx"

            raise FormatError(
                "String content does not contain a valid GPX XML signature"
            )

        raise FormatError(f"Unsupported content type: {type(content)}")

    except FormatError:
        raise
    except Exception as e:
        raise FormatError(f"Error detecting format: {e}") from e


def parse_any_format(content: Union[str, bytes], verbose: bool = False) -> RouteData:
    """
    Parse route data from GPX format.

    Supports:
    - str: GPX XML (XML signature detection)

    Uses strict validation - will raise FormatError on any invalid data.

    Args:
        content: Route data as string (GPX XML)
        verbose: If True, log detailed parsing information

    Returns:
        RouteData object with extracted track points

    Raises:
        FormatError: If format is invalid, unrecognized, or contains no valid data
    """
    try:
        format_type = detect_format(content)

        if verbose:
            logger.debug(f"Detected format: {format_type}")

        if format_type == "gpx":
            if verbose:
                logger.debug("Parsing as GPX format...")

            if isinstance(content, bytes):
                content = content.decode('utf-8')

            return gpx_to_route_data(content, verbose=verbose)

        raise FormatError(f"Unknown format type: {format_type}")

    except FormatError:
        raise
    except Exception as e:
        raise FormatError(f"Error parsing route data: {e}") from e


def _extract_bbox_from_route_data(route_data: RouteData) -> tuple:
    """
    Extract bounding box from RouteData.

    Args:
        route_data: RouteData object

    Returns:
        Tuple of (min_lat, max_lat, min_lon, max_lon)

    Raises:
        FormatError: If route has no valid points
    """
    return route_data.get_bounds()
