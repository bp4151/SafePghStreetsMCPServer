"""
Tests for format detection and unified parsing.

Verifies that format detection correctly identifies GPX and FIT files,
and that parse_any_format and parse_route_data work with both formats.
"""

import pytest
from pathlib import Path
import tempfile
import os

from server.converters import (
    detect_format,
    detect_format_from_filepath,
    parse_any_format,
    parse_route_data,
)
from server.format_models import RouteData, FormatError


def test_detect_format_gpx():
    """Test format detection for GPX content."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Test Route</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="40.42" lon="-79.93"/>
    </trkseg>
  </trk>
</gpx>"""
    
    detected = detect_format(gpx_content)
    assert detected == "gpx"


def test_detect_format_gpx_without_declaration():
    """Test format detection for GPX without XML declaration."""
    gpx_content = """<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk>
    <trkseg>
      <trkpt lat="40.42" lon="-79.93"/>
    </trkseg>
  </trk>
</gpx>"""
    
    detected = detect_format(gpx_content)
    assert detected == "gpx"


def test_detect_format_fit():
    """Test format detection for FIT content."""
    fit_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain.fit"
    
    if not fit_file_path.exists():
        pytest.skip(f"Sample FIT file not found at {fit_file_path}")
    
    with open(fit_file_path, 'rb') as f:
        fit_content = f.read()
    
    detected = detect_format(fit_content)
    assert detected == "fit"


def test_detect_format_invalid():
    """Test format detection for invalid content."""
    invalid_content = "This is just plain text, not GPX or FIT"
    
    with pytest.raises(FormatError, match="does not contain a valid GPX XML signature"):
        detect_format(invalid_content)


def test_detect_format_binary_invalid():
    """Test format detection for invalid binary content."""
    invalid_binary = b"This is binary but not a valid FIT file"
    
    with pytest.raises(FormatError, match=".FIT signature not found"):
        detect_format(invalid_binary)


def test_detect_format_too_small():
    """Test format detection for content that's too small."""
    tiny_content = b"x"
    
    with pytest.raises(FormatError, match="too small"):
        detect_format(tiny_content)


def test_detect_format_from_filepath_gpx():
    """Test filepath-based format detection for GPX."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gpx_path = os.path.join(tmpdir, "test_route.gpx")
        with open(gpx_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg><trkpt lat="40.42" lon="-79.93"/></trkseg></trk>
</gpx>""")
        
        detected = detect_format_from_filepath(gpx_path)
        assert detected == "gpx"


def test_detect_format_from_filepath_fit():
    """Test filepath-based format detection for FIT."""
    fit_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain.fit"
    
    if not fit_file_path.exists():
        pytest.skip(f"Sample FIT file not found at {fit_file_path}")
    
    detected = detect_format_from_filepath(str(fit_file_path))
    assert detected == "fit"


def test_detect_format_from_filepath_not_found():
    """Test filepath-based format detection when file doesn't exist."""
    with pytest.raises(FormatError, match="File not found"):
        detect_format_from_filepath("/nonexistent/path/file.gpx")


def test_detect_format_from_filepath_invalid_extension():
    """Test filepath-based format detection with unsupported extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = os.path.join(tmpdir, "test_route.txt")
        with open(invalid_path, 'w') as f:
            f.write("test")
        
        with pytest.raises(FormatError, match="Unrecognized file extension"):
            detect_format_from_filepath(invalid_path)


def test_parse_any_format_gpx():
    """Test parse_any_format with GPX content."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Test Route</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="40.42" lon="-79.93"/>
      <trkpt lat="40.43" lon="-79.92"/>
    </trkseg>
  </trk>
</gpx>"""
    
    route_data = parse_any_format(gpx_content)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) == 2
    assert route_data.metadata["format"] == "GPX"


def test_parse_any_format_gpx_with_verbose():
    """Test parse_any_format with GPX content and verbose logging."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Test Route</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="40.42" lon="-79.93"/>
    </trkseg>
  </trk>
</gpx>"""
    
    route_data = parse_any_format(gpx_content, verbose=True)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) == 1


def test_parse_any_format_fit():
    """Test parse_any_format with FIT file."""
    fit_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain.fit"
    
    if not fit_file_path.exists():
        pytest.skip(f"Sample FIT file not found at {fit_file_path}")
    
    with open(fit_file_path, 'rb') as f:
        fit_content = f.read()
    
    route_data = parse_any_format(fit_content)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) > 0
    assert route_data.metadata["format"] == "FIT"


def test_parse_any_format_fit_with_verbose():
    """Test parse_any_format with FIT file and verbose logging."""
    fit_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain.fit"
    
    if not fit_file_path.exists():
        pytest.skip(f"Sample FIT file not found at {fit_file_path}")
    
    with open(fit_file_path, 'rb') as f:
        fit_content = f.read()
    
    route_data = parse_any_format(fit_content, verbose=True)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) > 0


def test_parse_any_format_gpx_bytes_conversion():
    """GPX passed as bytes without .FIT signature is rejected."""
    gpx_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Test Route</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="40.42" lon="-79.93"/>
    </trkseg>
  </trk>
</gpx>"""

    with pytest.raises(FormatError, match=".FIT signature not found"):
        parse_any_format(gpx_content)


def test_parse_any_format_invalid():
    """Test parse_any_format with invalid content."""
    invalid_content = "Not a valid format"
    
    with pytest.raises(FormatError):
        parse_any_format(invalid_content)


def test_parse_any_format_strict_validation():
    """Test that strict validation rejects invalid coordinates."""
    invalid_gpx = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata>
    <name>Invalid Route</name>
  </metadata>
  <trk>
    <trkseg>
      <trkpt lat="200.0" lon="-79.93"/>
    </trkseg>
  </trk>
</gpx>"""
    
    with pytest.raises(FormatError, match="Invalid latitude"):
        parse_any_format(invalid_gpx)


def test_parse_route_data_gpx_filepath():
    """Test parse_route_data with explicit GPX filepath."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gpx_path = os.path.join(tmpdir, "test_route.gpx")
        with open(gpx_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <metadata><name>Test</name></metadata>
  <trk><trkseg>
    <trkpt lat="40.42" lon="-79.93"/>
    <trkpt lat="40.43" lon="-79.92"/>
  </trkseg></trk>
</gpx>""")
        
        route_data = parse_route_data(filepath=gpx_path)
        
        assert isinstance(route_data, RouteData)
        assert len(route_data.points) == 2
        assert route_data.metadata["format"] == "GPX"


def test_parse_route_data_fit_filepath():
    """Test parse_route_data with explicit FIT filepath."""
    fit_file_path = Path(__file__).parent.parent / "server" / "Home_Highland_Park_Fountain.fit"
    
    if not fit_file_path.exists():
        pytest.skip(f"Sample FIT file not found at {fit_file_path}")
    
    route_data = parse_route_data(filepath=str(fit_file_path))
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) > 0
    assert route_data.metadata["format"] == "FIT"


def test_parse_route_data_source_as_filepath():
    """Test parse_route_data with source as a filepath."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gpx_path = os.path.join(tmpdir, "test_route.gpx")
        with open(gpx_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg><trkpt lat="40.42" lon="-79.93"/></trkseg></trk>
</gpx>""")
        
        route_data = parse_route_data(source=gpx_path)
        
        assert isinstance(route_data, RouteData)
        assert len(route_data.points) == 1
        assert route_data.metadata["format"] == "GPX"


def test_parse_route_data_source_as_content():
    """Test parse_route_data with source as content (not filepath)."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg><trkpt lat="40.42" lon="-79.93"/></trkseg></trk>
</gpx>"""
    
    route_data = parse_route_data(source=gpx_content)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) == 1
    assert route_data.metadata["format"] == "GPX"


def test_parse_route_data_filepath_precedence():
    """Test that explicit filepath parameter takes precedence over source."""
    with tempfile.TemporaryDirectory() as tmpdir:
        gpx_path = os.path.join(tmpdir, "test_route.gpx")
        with open(gpx_path, 'w') as f:
            f.write("""<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg><trkpt lat="40.42" lon="-79.93"/></trkseg></trk>
</gpx>""")
        
        gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg>
    <trkpt lat="41.0" lon="-80.0"/>
    <trkpt lat="41.1" lon="-80.1"/>
    <trkpt lat="41.2" lon="-80.2"/>
  </trkseg></trk>
</gpx>"""
        
        route_data = parse_route_data(source=gpx_content, filepath=gpx_path)
        
        assert len(route_data.points) == 1


def test_parse_route_data_neither_source_nor_filepath():
    """Test parse_route_data raises error when neither source nor filepath provided."""
    with pytest.raises(ValueError, match="Either 'source' or 'filepath' must be provided"):
        parse_route_data()


def test_parse_route_data_with_verbose():
    """Test parse_route_data with verbose logging enabled."""
    gpx_content = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1">
  <trk><trkseg><trkpt lat="40.42" lon="-79.93"/></trkseg></trk>
</gpx>"""
    
    route_data = parse_route_data(source=gpx_content, verbose=True)
    
    assert isinstance(route_data, RouteData)
    assert len(route_data.points) == 1


def test_parse_route_data_nonexistent_filepath():
    """Test parse_route_data raises error for nonexistent filepath."""
    with pytest.raises(FormatError, match="File not found"):
        parse_route_data(filepath="/nonexistent/path/file.gpx")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
