"""
Contract tests for Export/Import and Trash APIs.

These tests validate the API contracts defined in specs/001-build-a-web/contracts/export-import.yaml
They MUST FAIL until views are implemented (TDD approach).

Tests cover:
- POST /api/v1/export - Export GPS points in multiple formats
- POST /api/v1/import - Import GPS points from files
- GET /api/v1/trash - List trashed points
- POST /api/v1/trash/{id}/restore - Restore point from trash
- DELETE /api/v1/trash/{id}/permanent - Permanently delete point
"""

import io
import json
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.contract
class TestExportImportContract:
    """
    Contract tests for Export/Import API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def authenticated_user_with_points(self, api_client):
        """Create user with GPS points."""
        # Register and authenticate
        register_url = reverse('authentication:register')
        register_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        access_token = response.data['access']
        user = response.data['user']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create GPS points
        point_url = reverse('points:list')
        point_ids = []
        for i in range(3):
            point_data = {
                'title': f'Test Point {i+1}',
                'latitude': 37.7749 + (i * 0.01),
                'longitude': -122.4194 + (i * 0.01),
                'tags': ['test', f'point{i+1}']
            }
            point_response = api_client.post(point_url, point_data, format='json')
            point_ids.append(point_response.data['id'])

        return api_client, user, point_ids

    # T036: POST /export - Export GPS points
    def test_export_geojson_success(self, authenticated_user_with_points):
        """
        Test exporting points as GeoJSON.

        Expected:
        - Status: 200 OK
        - Content-Type: application/geo+json
        - Response is valid GeoJSON FeatureCollection
        - Content-Disposition header with filename
        """
        api_client, user, point_ids = authenticated_user_with_points

        url = reverse('export_import:export')
        export_data = {
            'format': 'geojson',
            'point_ids': point_ids[:2],  # Export first 2 points
            'include_annotations': False
        }
        response = api_client.post(url, export_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'application/geo+json' in response['Content-Type'] or 'application/json' in response['Content-Type']
        assert 'Content-Disposition' in response
        assert 'geoannotator_export' in response['Content-Disposition']

        # Validate GeoJSON structure
        data = response.json() if hasattr(response, 'json') else json.loads(response.content)
        assert data['type'] == 'FeatureCollection'
        assert 'features' in data
        assert len(data['features']) == 2

    def test_export_gpx_success(self, authenticated_user_with_points):
        """
        Test exporting points as GPX.

        Expected:
        - Status: 200 OK
        - Content-Type: application/gpx+xml or application/xml
        - Response is valid GPX XML
        """
        api_client, user, point_ids = authenticated_user_with_points

        url = reverse('export_import:export')
        export_data = {
            'format': 'gpx'
        }
        response = api_client.post(url, export_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'xml' in response['Content-Type'].lower()
        assert 'Content-Disposition' in response

    def test_export_csv_success(self, authenticated_user_with_points):
        """
        Test exporting points as CSV.

        Expected:
        - Status: 200 OK
        - Content-Type: text/csv
        - Response contains CSV headers
        """
        api_client, user, point_ids = authenticated_user_with_points

        url = reverse('export_import:export')
        export_data = {
            'format': 'csv'
        }
        response = api_client.post(url, export_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'text/csv' in response['Content-Type']

        # Validate CSV headers
        content = response.content.decode('utf-8')
        assert 'latitude' in content.lower()
        assert 'longitude' in content.lower()
        assert 'title' in content.lower()

    def test_export_zip_with_annotations(self, authenticated_user_with_points):
        """
        Test exporting points as ZIP with annotations.

        Expected:
        - Status: 200 OK
        - Content-Type: application/zip
        - Response is valid ZIP archive
        """
        api_client, user, point_ids = authenticated_user_with_points

        url = reverse('export_import:export')
        export_data = {
            'format': 'zip'
        }
        response = api_client.post(url, export_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'application/zip' in response['Content-Type']
        assert '.zip' in response['Content-Disposition']

    def test_export_no_points_found(self, authenticated_user_with_points):
        """
        Test exporting with no matching points.

        Expected:
        - Status: 404 Not Found
        - error: NO_POINTS_FOUND
        """
        api_client, user, _ = authenticated_user_with_points

        url = reverse('export_import:export')
        export_data = {
            'format': 'geojson',
            'point_ids': ['00000000-0000-0000-0000-000000000000']
        }
        response = api_client.post(url, export_data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'NO_POINTS_FOUND'

    # T037: POST /import - Import GPS points
    def test_import_geojson_success(self, authenticated_user_with_points):
        """
        Test importing points from GeoJSON.

        Expected:
        - Status: 200 OK
        - Response contains: total_points, imported_points, skipped_points, failed_points, errors, created_point_ids
        - All points successfully imported
        """
        api_client, user, _ = authenticated_user_with_points

        # Create GeoJSON file
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-122.45, 37.80]
                    },
                    "properties": {
                        "title": "Imported Point 1",
                        "description": "Test import"
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-122.46, 37.81]
                    },
                    "properties": {
                        "title": "Imported Point 2"
                    }
                }
            ]
        }

        geojson_content = json.dumps(geojson_data).encode('utf-8')
        uploaded_file = SimpleUploadedFile(
            "points.geojson",
            geojson_content,
            content_type="application/geo+json"
        )

        url = reverse('export_import:import')
        data = {
            'format': 'geojson',
            'file': uploaded_file,
            'merge_strategy': 'create_new'
        }
        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_200_OK

        # Validate import result structure
        result = response.data
        assert 'total_points' in result
        assert 'imported_points' in result
        assert 'skipped_points' in result
        assert 'failed_points' in result
        assert 'errors' in result
        assert 'created_point_ids' in result

        assert result['total_points'] == 2
        assert result['imported_points'] == 2
        assert result['failed_points'] == 0
        assert len(result['created_point_ids']) == 2

    def test_import_csv_success(self, authenticated_user_with_points):
        """
        Test importing points from CSV.

        Expected:
        - CSV columns: latitude, longitude, title, description, tags
        - Points successfully imported
        """
        api_client, user, _ = authenticated_user_with_points

        # Create CSV file
        csv_content = """latitude,longitude,title,description,tags
37.82,-122.47,CSV Point 1,Test description,tag1|tag2
37.83,-122.48,CSV Point 2,,tag3
"""

        uploaded_file = SimpleUploadedFile(
            "points.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )

        url = reverse('export_import:import')
        data = {
            'format': 'csv',
            'file': uploaded_file,
            'merge_strategy': 'create_new'
        }
        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_points'] == 2
        assert response.data['imported_points'] == 2

    def test_import_validation_errors(self, authenticated_user_with_points):
        """
        Test importing with validation errors.

        Expected:
        - Status: 200 OK (partial success)
        - failed_points > 0
        - errors array contains per-point errors
        """
        api_client, user, _ = authenticated_user_with_points

        # GeoJSON with invalid coordinates
        geojson_data = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-200, 100]  # Invalid: lon > 180, lat > 90
                    },
                    "properties": {
                        "title": "Invalid Point"
                    }
                }
            ]
        }

        geojson_content = json.dumps(geojson_data).encode('utf-8')
        uploaded_file = SimpleUploadedFile(
            "invalid.geojson",
            geojson_content,
            content_type="application/geo+json"
        )

        url = reverse('export_import:import')
        data = {
            'format': 'geojson',
            'file': uploaded_file
        }
        response = api_client.post(url, data, format='multipart')

        # Should either be 200 with errors or 400 for invalid file
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

        if response.status_code == status.HTTP_200_OK:
            assert response.data['failed_points'] > 0
            assert len(response.data['errors']) > 0
            error = response.data['errors'][0]
            assert 'line_number' in error
            assert 'error' in error
            assert 'message' in error

    def test_import_invalid_format(self, authenticated_user_with_points):
        """
        Test importing with invalid file format.

        Expected:
        - Status: 400 Bad Request
        - error: INVALID_FORMAT
        """
        api_client, user, _ = authenticated_user_with_points

        # Invalid JSON
        uploaded_file = SimpleUploadedFile(
            "invalid.geojson",
            b"not valid json{",
            content_type="application/geo+json"
        )

        url = reverse('export_import:import')
        data = {
            'format': 'geojson',
            'file': uploaded_file
        }
        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'INVALID_FORMAT'


@pytest.mark.django_db
@pytest.mark.contract
@pytest.mark.critical
class TestTrashContract:
    """
    Contract tests for Trash API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def authenticated_user_with_trashed_point(self, api_client):
        """Create user with a trashed GPS point."""
        # Register and authenticate
        register_url = reverse('authentication:register')
        register_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        access_token = response.data['access']
        user = response.data['user']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create and delete a GPS point
        point_url = reverse('points:list')
        point_data = {
            'title': 'Point to Delete',
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        point_response = api_client.post(point_url, point_data, format='json')
        point_id = point_response.data['id']

        # Delete point (soft delete)
        delete_url = reverse('points:detail', kwargs={'pk': point_id})
        api_client.delete(delete_url)

        return api_client, user, point_id

    # T038: GET /trash - List trashed points
    def test_list_trash_success(self, authenticated_user_with_trashed_point):
        """
        Test listing trashed points.

        Expected:
        - Status: 200 OK
        - Response is array of TrashItem objects
        - Each item contains: id, gps_point, deleted_by, deleted_at, permanent_deletion_at, days_remaining
        """
        api_client, user, point_id = authenticated_user_with_trashed_point

        url = reverse('trash:points-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        results = response.data

        assert isinstance(results, list)
        assert len(results) == 1

        # Validate trash item structure
        item = results[0]
        assert 'id' in item
        assert 'gps_point' in item
        assert item['gps_point']['id'] == point_id
        assert 'deleted_by' in item
        assert item['deleted_by']['id'] == user['id']
        assert 'deleted_at' in item
        assert 'permanent_deletion_at' in item
        assert 'days_remaining' in item
        assert item['days_remaining'] <= 30

    # T039: POST /trash/{id}/restore - Restore point from trash
    def test_restore_point_success(self, authenticated_user_with_trashed_point):
        """
        Test restoring point from trash.

        Expected:
        - Status: 200 OK
        - Response contains restored point summary
        - Point is accessible again
        """
        api_client, user, point_id = authenticated_user_with_trashed_point

        url = reverse('trash:points-restore', kwargs={'pk': point_id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert response.data['id'] == point_id
        assert 'title' in response.data

        # Verify point is accessible
        point_url = reverse('points:detail', kwargs={'pk': point_id})
        get_response = api_client.get(point_url)
        assert get_response.status_code == status.HTTP_200_OK

    def test_restore_point_not_found(self, authenticated_user_with_trashed_point):
        """
        Test restoring non-existent point.

        Expected:
        - Status: 404 Not Found
        """
        api_client, user, _ = authenticated_user_with_trashed_point

        url = reverse('trash:points-restore', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # T040: DELETE /trash/{id}/permanent - Permanently delete point
    def test_permanently_delete_point_success(self, authenticated_user_with_trashed_point):
        """
        Test permanently deleting point from trash.

        Expected:
        - Status: 204 No Content
        - Point is permanently deleted (cannot be restored)
        """
        api_client, user, point_id = authenticated_user_with_trashed_point

        url = reverse('trash:points-permanent', kwargs={'pk': point_id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify point cannot be restored
        restore_url = reverse('trash:points-restore', kwargs={'pk': point_id})
        restore_response = api_client.post(restore_url)
        assert restore_response.status_code == status.HTTP_404_NOT_FOUND

    def test_permanently_delete_point_forbidden(self, api_client, authenticated_user_with_trashed_point):
        """
        Test permanently deleting point as non-owner.

        Expected:
        - Status: 403 Forbidden
        """
        owner_client, owner, point_id = authenticated_user_with_trashed_point

        # Create second user
        client2 = APIClient()
        register_url = reverse('authentication:register')
        register_data = {'email': 'user2@example.com', 'password': 'SecurePass123'}
        register_response = client2.post(register_url, register_data, format='json')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {register_response.data["access"]}')

        # Try to permanently delete as user2
        url = reverse('trash:points-permanent', kwargs={'pk': point_id})
        response = client2.delete(url)

        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
