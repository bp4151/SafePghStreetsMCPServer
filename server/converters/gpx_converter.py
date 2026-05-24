"""
GPX file format converter.

Converts XML-based GPX files to the common RouteData format.
"""

import logging
from typing import List

import gpxpy

from server.format_models import RouteData, TrackPoint, FormatError

logger = logging.getLogger(__name__)


def gpx_to_route_data(gpx_content: str, verbose: bool = False) -> RouteData:
    """
    Convert GPX XML format to RouteData.

    Supports tracks (<trk>/<trkseg>/<trkpt>), routes (<rte>/<rtept>),
    and waypoints (<wpt>).

    Args:
        gpx_content: XML string content of GPX file
        verbose: If True, log detailed parsing information

    Returns:
        RouteData object with extracted track points

    Raises:
        FormatError: If GPX file is invalid or has no valid track points
    """
    try:
        if verbose:
            logger.debug(f"Parsing GPX file ({len(gpx_content)} bytes)...")

        gpx = gpxpy.parse(gpx_content)

        if verbose:
            logger.debug(f"GPX parsed successfully. Name: {gpx.name}")

        route_name = gpx.name or "Imported GPX Route"
        track_points: List[TrackPoint] = []

        # Process tracks (<trk>) - most common for recorded activities
        if verbose:
            logger.debug(f"Processing {len(gpx.tracks)} tracks...")

        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    track_point = TrackPoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        elevation=point.elevation,
                        timestamp=point.time
                    )
                    track_points.append(track_point)

        if verbose:
            logger.debug(f"Extracted {len(track_points)} points from tracks")

        # Process routes (<rte>) - common for planned routes (cues)
        if verbose:
            logger.debug(f"Processing {len(gpx.routes)} routes...")

        for route in gpx.routes:
            for point in route.points:
                track_point = TrackPoint(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    elevation=point.elevation,
                    timestamp=point.time
                )
                track_points.append(track_point)

        if verbose:
            logger.debug(f"Total after routes: {len(track_points)} points")

        # Process waypoints (<wpt>) if no track/route points found
        if not track_points:
            if verbose:
                logger.debug(f"Processing {len(gpx.waypoints)} waypoints...")

            for waypoint in gpx.waypoints:
                track_point = TrackPoint(
                    latitude=waypoint.latitude,
                    longitude=waypoint.longitude,
                    elevation=waypoint.elevation,
                    timestamp=waypoint.time
                )
                track_points.append(track_point)

            if verbose:
                logger.debug(f"Extracted {len(track_points)} points from waypoints")

        if not track_points:
            raise FormatError("No valid track points found in GPX file")

        route_data = RouteData(
            name=route_name,
            points=track_points,
            metadata={
                "format": "GPX",
                "source": "GPX file",
                "point_count": len(track_points)
            }
        )

        if verbose:
            bounds = route_data.get_bounds()
            logger.debug(
                f"Route bounds: lat=[{bounds[0]:.5f}, {bounds[1]:.5f}], "
                f"lon=[{bounds[2]:.5f}, {bounds[3]:.5f}]"
            )

        return route_data

    except FormatError:
        raise
    except gpxpy.gpx.GPXException as e:
        raise FormatError(f"Failed to parse GPX file: {e}") from e
    except Exception as e:
        raise FormatError(f"Error parsing GPX file: {e}") from e
