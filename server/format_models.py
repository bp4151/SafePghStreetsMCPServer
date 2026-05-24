"""
Common data models for route format conversions.

This module defines the standard data structures used throughout the SafePghStreets
MCP server to represent GPS route data, regardless of input format (GPX, FIT, etc).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


class FormatError(Exception):
    """Exception raised for errors in route format parsing or validation."""
    pass


@dataclass
class TrackPoint:
    """Represents a single GPS coordinate point."""
    
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate coordinate ranges."""
        if not -90 <= self.latitude <= 90:
            raise FormatError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90.")
        if not -180 <= self.longitude <= 180:
            raise FormatError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180.")


@dataclass
class RouteData:
    """Represents a complete route with multiple track points."""
    
    name: str
    points: List[TrackPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate route data structure."""
        if not self.name or not isinstance(self.name, str):
            raise FormatError("Route must have a valid name (non-empty string).")
        
        if not self.points:
            raise FormatError("Route must have at least one track point.")
    
    def get_bounds(self) -> tuple:
        """
        Calculate bounding box for the route.
        
        Returns:
            Tuple of (min_lat, max_lat, min_lon, max_lon)
            
        Raises:
            FormatError: If route has no valid points.
        """
        if not self.points:
            raise FormatError("Cannot calculate bounds: route has no points.")
        
        lats = [p.latitude for p in self.points]
        lons = [p.longitude for p in self.points]
        
        return (min(lats), max(lats), min(lons), max(lons))
