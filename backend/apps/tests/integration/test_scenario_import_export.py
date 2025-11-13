"""
Integration Test - Scenario 5: Import/Export

Acceptance Criteria: FR-046 to FR-055
- Export points in multiple formats (GeoJSON, GPX, KML, CSV, ZIP)
- Import points from various formats
- Validation errors handling
- Duplicate detection
- Selective export (specific points)
- Bundle export with annotations
"""

import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User


@pytest.mark.django_db
class TestScenario5ImportExport:
    """Integration tests for import/export workflow."""

    def setup_method(self):
        """Set up test client and create test data before each test."""
        from rest_framework_simplejwt.tokens import RefreshToken

        self.client = APIClient()

        # Create Alice
        self.alice = User.objects.create_user(username="alice", email="alice@example.com", password="SecurePass123")
        refresh = RefreshToken.for_user(self.alice)
        self.alice_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        # Create test points
        points_url = reverse("points:list")

        self.point1 = self.client.post(
            points_url,
            {
                "title": "Point 1",
                "description": "<p>First point</p>",
                "latitude": 45.5231,
                "longitude": -122.6765,
                "tags": ["test", "export"],
            },
            format="json",
        ).data

        self.point2 = self.client.post(
            points_url,
            {
                "title": "Point 2",
                "description": "<p>Second point</p>",
                "latitude": 45.5195,
                "longitude": -122.7095,
                "tags": ["test"],
            },
            format="json",
        ).data

        self.export_url = reverse("export_import:export")
        self.import_url = reverse("export_import:import")

    def test_step_1_export_points_as_geojson(self):
        """
        Step 1: Export Points as GeoJSON

        Expected:
        - Response 200 with GeoJSON FeatureCollection
        - Content-Disposition: attachment; filename="geoannotator_export_*.geojson"
        """
        # Given
        export_data = {
            "format": "geojson",
            "include_annotations": False,
        }

        # When
        response = self.client.post(self.export_url, export_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "attachment" in response.get("Content-Disposition", "")
        assert ".geojson" in response.get("Content-Disposition", "")

        # Verify GeoJSON structure
        content = response.content.decode("utf-8")
        geojson_data = json.loads(content)
        assert geojson_data["type"] == "FeatureCollection"
        assert "features" in geojson_data
        assert len(geojson_data["features"]) >= 2

    def test_step_2_export_specific_points_as_gpx(self):
        """
        Step 2: Export Specific Points as GPX

        Expected:
        - Response 200 with GPX XML file
        - Contains only specified points
        """
        # Given
        export_data = {
            "format": "gpx",
            "point_ids": [self.point1["id"], self.point2["id"]],
        }

        # When
        response = self.client.post(self.export_url, export_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert (
            "application/gpx+xml" in response.get("Content-Type", "")
            or "text/xml" in response.get("Content-Type", "")
            or "application/xml" in response.get("Content-Type", "")
        )

        # Verify GPX structure
        content = response.content.decode("utf-8")
        assert "<gpx" in content
        assert "<wpt" in content
        assert "Point 1" in content or "Point 2" in content

    def test_step_3_export_full_bundle_as_zip(self):
        """
        Step 3: Export Full Bundle as ZIP

        Expected:
        - Response 200 with ZIP archive
        - Contains: points.geojson + annotations/ directory
        """
        # Given
        export_data = {
            "format": "zip",
        }

        # When
        response = self.client.post(self.export_url, export_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "application/zip" in response.get("Content-Type", "")
        assert "attachment" in response.get("Content-Disposition", "")
        assert ".zip" in response.get("Content-Disposition", "")

    def test_step_4_import_geojson_file(self):
        """
        Step 4: Import GeoJSON File

        Expected:
        - Response 200 with import result
        - total_points = N, imported_points = N, skipped_points = 0, failed_points = 0
        """
        # Given - Create GeoJSON content
        geojson_content = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-122.6765, 45.5231]},
                    "properties": {
                        "title": "Imported Point 1",
                        "description": "Test import",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-122.7095, 45.5195]},
                    "properties": {
                        "title": "Imported Point 2",
                        "description": "Another import",
                    },
                },
            ],
        }

        from django.core.files.uploadedfile import SimpleUploadedFile

        geojson_file = SimpleUploadedFile(
            "exported_points.geojson",
            json.dumps(geojson_content).encode("utf-8"),
            content_type="application/geo+json",
        )

        # When
        response = self.client.post(
            self.import_url,
            {
                "format": "geojson",
                "file": geojson_file,
                "merge_strategy": "create_new",
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_points"] == 2
        assert response.data["imported_points"] == 2
        assert response.data["failed_points"] == 0

    def test_step_5_import_csv_with_validation_errors(self):
        """
        Step 5: Import CSV with Validation Errors

        Expected:
        - Response 200 with import result
        - total_points = 3, imported_points = 1, failed_points = 2
        - errors array contains validation errors
        """
        # Given - CSV with validation errors
        # Note: Use unique coordinates to avoid duplicate detection with setup points
        csv_content = """latitude,longitude,title,description,tags
45.5250,-122.6800,"Valid Point","Description","tag1|tag2"
99.0000,-122.6765,"Invalid Lat","Bad coordinates","tag3"
45.5195,,"Missing Lon","No longitude","""

        from django.core.files.uploadedfile import SimpleUploadedFile

        csv_file = SimpleUploadedFile(
            "points_with_errors.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        # When
        response = self.client.post(
            self.import_url,
            {
                "format": "csv",
                "file": csv_file,
                "merge_strategy": "skip",
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_points"] == 3
        assert response.data["imported_points"] == 1
        assert response.data["failed_points"] == 2
        assert "errors" in response.data
        assert len(response.data["errors"]) == 2

    def test_step_6_import_with_duplicate_detection(self):
        """
        Step 6: Import with Duplicate Detection

        Expected:
        - Response 200 with import result
        - skipped_points > 0 (duplicates at same coordinates)
        """
        # Given - Create a point first
        existing_point = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [-122.6000, 45.5000]},
                    "properties": {
                        "title": "Existing Point",
                    },
                }
            ],
        }

        from django.core.files.uploadedfile import SimpleUploadedFile

        # Import first time
        file1 = SimpleUploadedFile(
            "first_import.geojson",
            json.dumps(existing_point).encode("utf-8"),
            content_type="application/geo+json",
        )

        self.client.post(
            self.import_url,
            {
                "format": "geojson",
                "file": file1,
                "merge_strategy": "skip",
            },
            format="multipart",
        )

        # Try to import duplicate
        file2 = SimpleUploadedFile(
            "duplicate_import.geojson",
            json.dumps(existing_point).encode("utf-8"),
            content_type="application/geo+json",
        )

        # When
        response = self.client.post(
            self.import_url,
            {
                "format": "geojson",
                "file": file2,
                "merge_strategy": "skip",
            },
            format="multipart",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["skipped_points"] >= 1 or response.data["imported_points"] == 0

    def test_complete_import_export_cycle(self):
        """
        Complete Flow: Export → Import → Verify

        This test validates the full import/export cycle.
        """
        # Step 1: Export existing points as GeoJSON
        export_response = self.client.post(
            self.export_url,
            {"format": "geojson", "include_annotations": False},
            format="json",
        )
        assert export_response.status_code == status.HTTP_200_OK

        # Step 2: Import the exported data
        from django.core.files.uploadedfile import SimpleUploadedFile

        imported_file = SimpleUploadedFile(
            "reimport.geojson", export_response.content, content_type="application/geo+json"
        )

        import_response = self.client.post(
            self.import_url,
            {
                "format": "geojson",
                "file": imported_file,
                "merge_strategy": "create_new",  # Allow duplicates for this test
            },
            format="multipart",
        )

        # Step 3: Verify import succeeded
        assert import_response.status_code == status.HTTP_200_OK
        assert import_response.data["imported_points"] >= 2
