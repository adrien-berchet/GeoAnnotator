"""
Unit tests for point type export/import functionality.

Tests that point types are correctly exported and imported across different formats.
"""

import csv
import io
import json
import xml.etree.ElementTree as ET

import pytest

from apps.export_import.services import ExportService
from apps.export_import.services import ImportService
from apps.points.models import GPSPoint
from apps.points.models import PointType


@pytest.mark.django_db
def test_export_geojson_includes_point_type(alice, gps_point_alice):
    """Test that GeoJSON export includes point type name and icon."""
    # Create a custom point type
    point_type = PointType.objects.create(
        type_choice="custom",
        names={"en": "Restaurant", "fr": "Restaurant"},
        creation_language="en",
        icon="🍴",
        owner=alice,
        visibility="private",
        status="active",
    )
    gps_point_alice.type = point_type
    gps_point_alice.save()

    # Export
    geojson_str = ExportService.export_geojson([gps_point_alice], include_annotations=False)
    data = json.loads(geojson_str)

    # Verify point type is included
    feature = data["features"][0]
    assert feature["properties"]["point_type"] == "Restaurant"
    assert feature["properties"]["point_type_icon"] == "🍴"


@pytest.mark.django_db
def test_export_geojson_without_point_type(gps_point_alice):
    """Test that GeoJSON export handles points without a type."""
    # Ensure point has no type
    gps_point_alice.type = None
    gps_point_alice.save()

    # Export
    geojson_str = ExportService.export_geojson([gps_point_alice], include_annotations=False)
    data = json.loads(geojson_str)

    # Verify point type fields are None
    feature = data["features"][0]
    assert feature["properties"]["point_type"] is None
    assert feature["properties"]["point_type_icon"] is None


@pytest.mark.django_db
def test_export_csv_includes_point_type(alice, gps_point_alice):
    """Test that CSV export includes point type column."""
    # Create a custom point type
    point_type = PointType.objects.create(
        type_choice="custom",
        names={"en": "Museum", "fr": "Musée"},
        creation_language="en",
        icon="🏛️",
        owner=alice,
        visibility="private",
        status="active",
    )
    gps_point_alice.type = point_type
    gps_point_alice.save()

    # Export
    csv_str = ExportService.export_csv([gps_point_alice])

    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)

    # Verify point type is included
    assert "point_type" in rows[0]
    assert rows[0]["point_type"] == "Museum"


@pytest.mark.django_db
def test_export_kml_includes_point_type(alice, gps_point_alice):
    """Test that KML export includes point type in extended data."""
    # Create a custom point type
    point_type = PointType.objects.create(
        type_choice="custom",
        names={"en": "Park", "fr": "Parc"},
        creation_language="en",
        icon="🌳",
        owner=alice,
        visibility="private",
        status="active",
    )
    gps_point_alice.type = point_type
    gps_point_alice.save()

    # Export
    kml_str = ExportService.export_kml([gps_point_alice])

    # Parse KML
    root = ET.fromstring(kml_str.encode())
    ns = {"kml": "http://www.opengis.net/kml/2.2"}

    # Find extended data
    extended_data = root.find(".//kml:ExtendedData", ns)
    assert extended_data is not None

    # Find point_type data element
    point_type_data = None
    point_type_icon_data = None
    for data_elem in extended_data.findall("kml:Data", ns):
        if data_elem.get("name") == "point_type":
            point_type_data = data_elem.find("kml:value", ns)
        elif data_elem.get("name") == "point_type_icon":
            point_type_icon_data = data_elem.find("kml:value", ns)

    assert point_type_data is not None
    assert point_type_data.text == "Park"
    assert point_type_icon_data is not None
    assert point_type_icon_data.text == "🌳"


@pytest.mark.django_db
def test_import_geojson_creates_missing_point_type(alice):
    """Test that importing GeoJSON creates missing point types automatically."""
    # Create GeoJSON with a point type that doesn't exist
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]},
                "properties": {
                    "title": "Eiffel Tower",
                    "description": "Iconic Paris landmark",
                    "point_type": "Monument",
                    "point_type_icon": "🗼",
                    "tags": [],
                    "is_public": False,
                },
            }
        ],
    }

    geojson_str = json.dumps(geojson_data)

    # Import
    result = ImportService.import_geojson(geojson_str, alice, "create_new")

    # Verify import succeeded
    assert result["imported_points"] == 1
    assert result["failed_points"] == 0

    # Verify point was created with correct type
    point = GPSPoint.objects.get(title="Eiffel Tower")
    assert point.type is not None
    assert point.type.names["en"] == "Monument"
    assert point.type.icon == "🗼"
    assert point.type.owner == alice
    assert point.type.type_choice == "custom"
    assert point.type.status == "active"


@pytest.mark.django_db
def test_import_geojson_uses_existing_point_type(alice):
    """Test that importing GeoJSON uses existing point type if available."""
    # Create a point type
    existing_type = PointType.objects.create(
        type_choice="custom",
        names={"en": "Cafe", "fr": "Café"},
        creation_language="en",
        icon="☕",
        owner=alice,
        visibility="private",
        status="active",
    )

    # Create GeoJSON with the same point type name
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]},
                "properties": {
                    "title": "Paris Cafe",
                    "point_type": "Cafe",
                    "tags": [],
                    "is_public": False,
                },
            }
        ],
    }

    geojson_str = json.dumps(geojson_data)

    # Import
    result = ImportService.import_geojson(geojson_str, alice, "create_new")

    # Verify import succeeded
    assert result["imported_points"] == 1

    # Verify point uses existing type (not a new one)
    point = GPSPoint.objects.get(title="Paris Cafe")
    assert point.type == existing_type

    # Verify no duplicate type was created
    assert PointType.objects.filter(names__en="Cafe", owner=alice).count() == 1


@pytest.mark.django_db
def test_import_csv_creates_missing_point_type(alice):
    """Test that importing CSV creates missing point types automatically."""
    csv_content = """title,latitude,longitude,point_type,tags,is_public
Central Park,40.785091,-73.968285,Park,nature|recreation,false"""

    # Import
    result = ImportService.import_csv(csv_content, alice, "create_new")

    # Verify import succeeded
    assert result["imported_points"] == 1
    assert result["failed_points"] == 0

    # Verify point was created with correct type
    point = GPSPoint.objects.get(title="Central Park")
    assert point.type is not None
    assert point.type.names["en"] == "Park"
    assert point.type.icon == "📍"  # Default icon
    assert point.type.owner == alice


@pytest.mark.django_db
def test_import_kml_creates_missing_point_type(alice):
    """Test that importing KML creates missing point types automatically."""
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Golden Gate Bridge</name>
      <description>Famous San Francisco bridge</description>
      <Point>
        <coordinates>-122.4783,37.8199</coordinates>
      </Point>
      <ExtendedData>
        <Data name="point_type">
          <value>Bridge</value>
        </Data>
        <Data name="point_type_icon">
          <value>🌉</value>
        </Data>
        <Data name="is_public">
          <value>false</value>
        </Data>
      </ExtendedData>
    </Placemark>
  </Document>
</kml>"""

    # Import
    result = ImportService.import_kml(kml_content, alice, "create_new")

    # Verify import succeeded
    assert result["imported_points"] == 1
    assert result["failed_points"] == 0

    # Verify point was created with correct type
    point = GPSPoint.objects.get(title="Golden Gate Bridge")
    assert point.type is not None
    assert point.type.names["en"] == "Bridge"
    assert point.type.icon == "🌉"
    assert point.type.owner == alice


@pytest.mark.django_db
def test_import_geojson_replace_updates_point_type(alice):
    """Test that replace strategy updates point type on existing points."""
    # Create a point type and a point
    old_type = PointType.objects.create(
        type_choice="custom",
        names={"en": "Old Type"},
        creation_language="en",
        icon="📌",
        owner=alice,
        visibility="private",
        status="active",
    )

    from apps.points.services import PointService

    existing_point = PointService.create_point(
        title="Test Point",
        latitude=48.8566,
        longitude=2.3522,
        owner=alice,
    )
    existing_point.type = old_type
    existing_point.save()

    # Create GeoJSON with different point type at same location
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [2.3522, 48.8566]},
                "properties": {
                    "title": "Updated Point",
                    "point_type": "New Type",
                    "point_type_icon": "🎯",
                    "tags": [],
                    "is_public": False,
                },
            }
        ],
    }

    geojson_str = json.dumps(geojson_data)

    # Import with replace strategy
    result = ImportService.import_geojson(geojson_str, alice, "replace")

    # Verify point was updated
    assert result["imported_points"] == 1
    assert result["skipped_points"] == 0

    # Refresh point
    existing_point.refresh_from_db()

    # Verify type was updated
    assert existing_point.type is not None
    assert existing_point.type.names["en"] == "New Type"
    assert existing_point.type.icon == "🎯"
    assert existing_point.type != old_type
