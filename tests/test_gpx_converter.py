"""
Tests for GPX format converter.

Verifies that GPX files are correctly parsed into RouteData format.
"""

import pytest
from pathlib import Path

from server.converters.gpx_converter import gpx_to_route_data
from server.format_models import RouteData, FormatError


def test_gpx_converter_with_sample_file():
    """Test parsing the sample Highland Park GPX file."""
    gpx_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain_cues.gpx"
    
    if not gpx_file_path.exists():
        pytest.skip(f"Sample GPX file not found at {gpx_file_path}")
    
    with open(gpx_file_path, 'r', encoding='utf-8') as f:
        gpx_content = f.read()
    
    # Parse the GPX file
    route_data = gpx_to_route_data(gpx_content, verbose=False)
    
    # Verify basic structure
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) > 0
    assert route_data.name is not None
    assert route_data.metadata["format"] == "GPX"
    
    # Verify bounds calculation
    bounds = route_data.get_bounds()
    assert len(bounds) == 4
    min_lat, max_lat, min_lon, max_lon = bounds
    
    assert min_lat < max_lat
    assert min_lon < max_lon
    assert -90 <= min_lat <= 90
    assert -90 <= max_lat <= 90
    assert -180 <= min_lon <= 180
    assert -180 <= max_lon <= 180


def test_gpx_converter_with_verbose_logging():
    """Test parsing with verbose logging enabled."""
    gpx_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain_cues.gpx"
    
    if not gpx_file_path.exists():
        pytest.skip(f"Sample GPX file not found at {gpx_file_path}")
    
    with open(gpx_file_path, 'r', encoding='utf-8') as f:
        gpx_content = f.read()
    
    # Parse with verbose logging (should not raise)
    route_data = gpx_to_route_data(gpx_content, verbose=True)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) > 0


def test_gpx_converter_invalid_xml():
    """Test error handling for invalid XML."""
    invalid_gpx = "<invalid>not a gpx file</invalid>"
    
    with pytest.raises(FormatError):
        gpx_to_route_data(invalid_gpx)


def test_gpx_converter_empty_route():
    """Test error handling for GPX with no track points."""
    empty_gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Empty Route</name>
  </metadata>
  <trk>
    <trkseg>
    </trkseg>
  </trk>
</gpx>"""
    
    with pytest.raises(FormatError, match="No valid track points"):
        gpx_to_route_data(empty_gpx)


def test_gpx_converter_validates_coordinates():
    """Test that invalid coordinates are rejected."""
    # GPX with invalid latitude (> 90)
    invalid_coords_gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Invalid Coords</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="191.0" lon="-79.0"/>
    </trkseg>
  </trk>
</gpx>"""
    
    with pytest.raises(FormatError, match="Invalid latitude"):
        gpx_to_route_data(invalid_coords_gpx)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
