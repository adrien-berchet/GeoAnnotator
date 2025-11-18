"""
Unit tests for export_import serializers.

Tests validation for export and import requests.
"""

import uuid

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.export_import.serializers import ExportRequestSerializer
from apps.export_import.serializers import ImportRequestSerializer
from apps.export_import.serializers import ImportResultSerializer


class TestExportRequestSerializer:
    """Test ExportRequestSerializer."""

    def test_validate_format_geojson_passes(self, api_request_factory, alice):
        """GeoJSON format should be valid."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "geojson"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "geojson"

    def test_validate_format_gpx_passes(self, api_request_factory, alice):
        """GPX format should be valid."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "gpx"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "gpx"

    def test_validate_format_kml_passes(self, api_request_factory, alice):
        """KML format should be valid."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "kml"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "kml"

    def test_validate_format_csv_passes(self, api_request_factory, alice):
        """CSV format should be valid."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "csv"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "csv"

    def test_validate_format_zip_passes(self, api_request_factory, alice):
        """ZIP format should be valid."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "zip"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "zip"

    def test_validate_format_invalid_fails(self, api_request_factory, alice):
        """Invalid format should fail."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "invalid"}
        serializer = ExportRequestSerializer(data=data, context={"request": request})

        assert not serializer.is_valid()
        assert "format" in serializer.errors
        # DRF ChoiceField validates before custom validate_format method
        assert "not a valid choice" in str(serializer.errors["format"])

    def test_validate_point_ids_empty_passes(self, api_request_factory, alice):
        """Empty point IDs list should pass."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "geojson", "point_ids": []}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

    def test_validate_point_ids_nonexistent_fails(self, api_request_factory, alice):
        """Nonexistent point ID should fail."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        fake_id = uuid.uuid4()
        data = {"format": "geojson", "point_ids": [str(fake_id)]}
        serializer = ExportRequestSerializer(data=data, context={"request": request})

        assert not serializer.is_valid()
        assert "point_ids" in serializer.errors
        assert "does not exist" in str(serializer.errors["point_ids"])

    def test_validate_point_ids_no_access_fails(
        self, api_request_factory, alice, bob, gps_point_alice
    ):
        """Point without access should fail."""
        request = api_request_factory.post("/api/export/")
        request.user = bob  # Bob tries to export Alice's private point

        data = {"format": "geojson", "point_ids": [str(gps_point_alice.id)]}
        serializer = ExportRequestSerializer(data=data, context={"request": request})

        assert not serializer.is_valid()
        assert "point_ids" in serializer.errors

    def test_validate_point_ids_with_access_passes(
        self, api_request_factory, alice, gps_point_alice
    ):
        """Point with access should pass."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {"format": "geojson", "point_ids": [str(gps_point_alice.id)]}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

    def test_validate_point_ids_public_point_passes(
        self, api_request_factory, bob, public_gps_point_alice
    ):
        """Public point should be accessible by anyone."""
        request = api_request_factory.post("/api/export/")
        request.user = bob

        data = {"format": "geojson", "point_ids": [str(public_gps_point_alice.id)]}
        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

    def test_serializer_with_valid_data(self, api_request_factory, alice, gps_point_alice):
        """Valid export request should pass."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {
            "format": "geojson",
            "point_ids": [str(gps_point_alice.id)],
            "include_annotations": True,
        }

        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)

    def test_serializer_without_point_ids(self, api_request_factory, alice):
        """Export request without point IDs should pass."""
        request = api_request_factory.post("/api/export/")
        request.user = alice

        data = {
            "format": "csv",
            "include_annotations": False,
        }

        serializer = ExportRequestSerializer(data=data, context={"request": request})
        assert serializer.is_valid(raise_exception=True)


class TestImportRequestSerializer:
    """Test ImportRequestSerializer."""

    def test_validate_format_geojson_passes(self):
        """GeoJSON format should be valid."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "geojson"

    def test_validate_format_gpx_passes(self):
        """GPX format should be valid."""
        file = SimpleUploadedFile("track.gpx", b"<gpx></gpx>")
        data = {"format": "gpx", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "gpx"

    def test_validate_format_kml_passes(self):
        """KML format should be valid."""
        file = SimpleUploadedFile("places.kml", b"<kml></kml>")
        data = {"format": "kml", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "kml"

    def test_validate_format_csv_passes(self):
        """CSV format should be valid."""
        file = SimpleUploadedFile("points.csv", b"lat,lon,name\n45.0,-122.0,Test")
        data = {"format": "csv", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["format"] == "csv"

    def test_validate_format_zip_fails(self):
        """ZIP format should not be valid for import."""
        file = SimpleUploadedFile("data.zip", b"PK\x03\x04")
        data = {"format": "zip", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "format" in serializer.errors

    def test_validate_format_invalid_fails(self):
        """Invalid format should fail."""
        file = SimpleUploadedFile("data.txt", b"content")
        data = {"format": "invalid", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "format" in serializer.errors

    def test_validate_file_within_limit_passes(self):
        """File within size limit should pass."""
        file = SimpleUploadedFile("test.csv", b"content")
        data = {"format": "csv", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_file_exceeds_limit_fails(self):
        """File exceeding size limit should fail."""
        # Create a file larger than 100MB
        large_content = b"x" * (101 * 1024 * 1024)
        file = SimpleUploadedFile("large.csv", large_content)
        data = {"format": "csv", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "file" in serializer.errors
        assert "exceeds maximum" in str(serializer.errors["file"])

    def test_validate_geojson_with_geojson_extension_passes(self):
        """GeoJSON file with .geojson extension should pass."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_geojson_with_json_extension_passes(self):
        """GeoJSON file with .json extension should pass."""
        file = SimpleUploadedFile("data.json", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_gpx_with_gpx_extension_passes(self):
        """GPX file with .gpx extension should pass."""
        file = SimpleUploadedFile("track.gpx", b"<gpx></gpx>")
        data = {"format": "gpx", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_kml_with_kml_extension_passes(self):
        """KML file with .kml extension should pass."""
        file = SimpleUploadedFile("places.kml", b"<kml></kml>")
        data = {"format": "kml", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_csv_with_csv_extension_passes(self):
        """CSV file with .csv extension should pass."""
        file = SimpleUploadedFile("points.csv", b"lat,lon,name\n45.0,-122.0,Test")
        data = {"format": "csv", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_validate_extension_mismatch_fails(self):
        """File extension not matching format should fail."""
        file = SimpleUploadedFile("data.csv", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert not serializer.is_valid()
        assert "file" in serializer.errors
        assert "extension does not match format" in str(serializer.errors["file"])

    def test_validate_with_merge_strategy_create_new(self):
        """Create new merge strategy should be valid."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file, "merge_strategy": "create_new"}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["merge_strategy"] == "create_new"

    def test_validate_with_merge_strategy_skip(self):
        """Skip merge strategy should be valid."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file, "merge_strategy": "skip"}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["merge_strategy"] == "skip"

    def test_validate_with_merge_strategy_replace(self):
        """Replace merge strategy should be valid."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file, "merge_strategy": "replace"}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["merge_strategy"] == "replace"

    def test_validate_default_merge_strategy(self):
        """Default merge strategy should be create_new."""
        file = SimpleUploadedFile("data.geojson", b'{"type": "FeatureCollection"}')
        data = {"format": "geojson", "file": file}

        serializer = ImportRequestSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)
        assert serializer.validated_data["merge_strategy"] == "create_new"


class TestImportResultSerializer:
    """Test ImportResultSerializer."""

    def test_serializer_with_all_fields(self):
        """Serializer should accept all fields."""
        data = {
            "total_points": 10,
            "imported_points": 8,
            "skipped_points": 1,
            "failed_points": 1,
            "errors": [{"line_number": 5, "error": "INVALID_DATA", "message": "Missing field"}],
        }

        serializer = ImportResultSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_serializer_without_errors(self):
        """Serializer should work without errors field."""
        data = {
            "total_points": 5,
            "imported_points": 5,
            "skipped_points": 0,
            "failed_points": 0,
        }

        serializer = ImportResultSerializer(data=data)
        assert serializer.is_valid(raise_exception=True)

    def test_serializer_output(self):
        """Serializer should output correct data."""
        data = {
            "total_points": 3,
            "imported_points": 2,
            "skipped_points": 1,
            "failed_points": 0,
        }

        serializer = ImportResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        assert serializer.validated_data["total_points"] == 3
        assert serializer.validated_data["imported_points"] == 2
        assert serializer.validated_data["skipped_points"] == 1
        assert serializer.validated_data["failed_points"] == 0
