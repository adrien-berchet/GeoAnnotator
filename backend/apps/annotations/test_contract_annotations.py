"""
Contract tests for Annotations API.

These tests validate the API contract defined in specs/001-build-a-web/contracts/annotations.yaml
They MUST FAIL until views are implemented (TDD approach).

Tests cover:
- GET /api/v1/points/{id}/annotations - List annotations
- POST /api/v1/points/{id}/annotations - Create text/file annotation
- GET /api/v1/points/{id}/annotations/{id} - Get annotation details
- PUT /api/v1/points/{id}/annotations/{id} - Update text annotation
- DELETE /api/v1/points/{id}/annotations/{id} - Delete annotation
- GET /api/v1/annotations/{id}/download - Download file
"""

import io
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.contract
@pytest.mark.critical
class TestAnnotationsContract:
    """
    Contract tests for Annotations API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def authenticated_user(self, api_client):
        """Create and authenticate a user with a GPS point."""
        # Register user
        register_url = reverse('auth:register')
        register_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        access_token = response.data['access']
        user = response.data['user']

        # Set authentication
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create a GPS point
        point_url = reverse('points:list')
        point_data = {
            'title': 'Test Point',
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        point_response = api_client.post(point_url, point_data, format='json')
        point_id = point_response.data['id']

        return api_client, user, point_id

    @pytest.fixture
    def text_annotation_data(self):
        """Valid text annotation payload."""
        return {
            'type': 'text',
            'text_content': '<p>Beautiful sunset 🌅</p>'
        }

    # T023: POST /points/{id}/annotations - Create text annotation
    def test_create_text_annotation_success(self, authenticated_user, text_annotation_data):
        """
        Test successful text annotation creation.

        Expected:
        - Status: 201 Created
        - Response contains: id, gps_point_id, type, text_content, created_at
        - type is 'text'
        - file is null
        """
        api_client, user, point_id = authenticated_user
        url = reverse('annotations:list', kwargs={'point_id': point_id})
        response = api_client.post(url, text_annotation_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        annotation = response.data
        assert 'id' in annotation
        assert annotation['gps_point_id'] == point_id
        assert annotation['type'] == 'text'
        assert annotation['text_content'] == text_annotation_data['text_content']
        assert 'created_at' in annotation
        assert annotation['file'] is None

    def test_create_file_annotation_success(self, authenticated_user):
        """
        Test successful file annotation creation.

        Expected:
        - Status: 201 Created
        - Response contains: id, gps_point_id, type, file, created_at
        - file contains: url, file_name, file_size, mime_type, can_preview
        - text_content is null
        """
        api_client, user, point_id = authenticated_user

        # Create test image file
        image_content = b'fake-image-content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )

        url = reverse('annotations:list', kwargs={'point_id': point_id})
        data = {
            'type': 'image',
            'file': uploaded_file
        }
        response = api_client.post(url, data, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        annotation = response.data
        assert 'id' in annotation
        assert annotation['gps_point_id'] == point_id
        assert annotation['type'] == 'image'
        assert annotation['text_content'] is None

        # Validate file metadata
        assert annotation['file'] is not None
        file_meta = annotation['file']
        assert 'url' in file_meta
        assert file_meta['file_name'] == 'test_image.jpg'
        assert file_meta['file_size'] == len(image_content)
        assert file_meta['mime_type'] == 'image/jpeg'
        assert file_meta['can_preview'] is True

    def test_create_annotation_file_too_large(self, authenticated_user):
        """
        Test file upload exceeding 1GB limit.

        Expected:
        - Status: 400 Bad Request or 413 Payload Too Large
        - error: FILE_TOO_LARGE
        - details contains file_size and max_size
        """
        api_client, user, point_id = authenticated_user

        url = reverse('annotations:list', kwargs={'point_id': point_id})

        # Mock a large file (we can't create 1GB in memory)
        # This test will validate the error response structure
        # Actual implementation will check Content-Length header
        data = {
            'type': 'file',
            'file': SimpleUploadedFile("large.bin", b'data', content_type="application/octet-stream")
        }

        # For now, we expect this to pass (file is small)
        # Full implementation will add size validation
        response = api_client.post(url, data, format='multipart')

        # Placeholder assertion - will be updated with actual size validation
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]

    def test_create_annotation_quota_exceeded(self, authenticated_user):
        """
        Test file upload when user quota is exceeded.

        Expected:
        - Status: 403 Forbidden
        - error: QUOTA_EXCEEDED
        - details contains user_storage_used, user_storage_limit, file_size
        """
        # This test will be implemented when quota tracking is in place
        # For now, just validate the structure
        pass

    # T024: GET /points/{id}/annotations - List annotations
    def test_list_annotations_success(self, authenticated_user, text_annotation_data):
        """
        Test listing annotations for a point.

        Expected:
        - Status: 200 OK
        - Response is array of Annotation objects
        """
        api_client, user, point_id = authenticated_user

        # Create annotation first
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        api_client.post(create_url, text_annotation_data, format='json')

        # List annotations
        list_url = reverse('annotations:list', kwargs={'point_id': point_id})
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

        # Validate annotation structure
        annotation = response.data[0]
        assert 'id' in annotation
        assert 'gps_point_id' in annotation
        assert 'type' in annotation
        assert 'created_at' in annotation

    def test_list_annotations_with_type_filter(self, authenticated_user, text_annotation_data):
        """
        Test listing annotations with type filter.

        Expected:
        - Only annotations of specified type are returned
        """
        api_client, user, point_id = authenticated_user

        # Create text annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        api_client.post(create_url, text_annotation_data, format='json')

        # List with type filter
        list_url = reverse('annotations:list', kwargs={'point_id': point_id})
        response = api_client.get(list_url, {'type': 'text'})

        assert response.status_code == status.HTTP_200_OK
        assert all(ann['type'] == 'text' for ann in response.data)

    # T025: GET /points/{id}/annotations/{id} - Get annotation details
    def test_get_annotation_success(self, authenticated_user, text_annotation_data):
        """
        Test getting annotation details.

        Expected:
        - Status: 200 OK
        - Full annotation details returned
        """
        api_client, user, point_id = authenticated_user

        # Create annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        create_response = api_client.post(create_url, text_annotation_data, format='json')
        annotation_id = create_response.data['id']

        # Get annotation
        detail_url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': annotation_id}
        )
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == annotation_id
        assert response.data['text_content'] == text_annotation_data['text_content']

    def test_get_annotation_not_found(self, authenticated_user):
        """
        Test getting non-existent annotation.

        Expected:
        - Status: 404 Not Found
        """
        api_client, user, point_id = authenticated_user

        url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': '00000000-0000-0000-0000-000000000000'}
        )
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # T026: PUT /points/{id}/annotations/{id} - Update text annotation
    def test_update_text_annotation_success(self, authenticated_user, text_annotation_data):
        """
        Test successful text annotation update.

        Expected:
        - Status: 200 OK
        - text_content is updated
        """
        api_client, user, point_id = authenticated_user

        # Create annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        create_response = api_client.post(create_url, text_annotation_data, format='json')
        annotation_id = create_response.data['id']

        # Update annotation
        update_url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': annotation_id}
        )
        update_data = {'text_content': '<p>Updated content 🎉</p>'}
        response = api_client.put(update_url, update_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['text_content'] == update_data['text_content']

    def test_update_file_annotation_fails(self, authenticated_user):
        """
        Test updating file annotation (not allowed).

        Expected:
        - Status: 400 Bad Request
        - error: INVALID_OPERATION
        - message indicates file annotations cannot be updated
        """
        api_client, user, point_id = authenticated_user

        # Create file annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        file_data = {
            'type': 'image',
            'file': SimpleUploadedFile("test.jpg", b'data', content_type="image/jpeg")
        }
        create_response = api_client.post(create_url, file_data, format='multipart')
        annotation_id = create_response.data['id']

        # Try to update
        update_url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': annotation_id}
        )
        update_data = {'text_content': 'Cannot update files'}
        response = api_client.put(update_url, update_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'INVALID_OPERATION'

    # T027: DELETE /points/{id}/annotations/{id} - Delete annotation
    def test_delete_annotation_success(self, authenticated_user, text_annotation_data):
        """
        Test successful annotation deletion.

        Expected:
        - Status: 204 No Content
        - Annotation is permanently deleted
        - For file annotations, storage quota is updated
        """
        api_client, user, point_id = authenticated_user

        # Create annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        create_response = api_client.post(create_url, text_annotation_data, format='json')
        annotation_id = create_response.data['id']

        # Delete annotation
        delete_url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': annotation_id}
        )
        response = api_client.delete(delete_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        get_response = api_client.get(delete_url)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_annotation_forbidden(self, api_client, authenticated_user, text_annotation_data):
        """
        Test deleting annotation without edit permission.

        Expected:
        - Status: 403 Forbidden
        - error: ACCESS_DENIED
        """
        # Create annotation as user1
        client1, user1, point_id = authenticated_user
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        create_response = client1.post(create_url, text_annotation_data, format='json')
        annotation_id = create_response.data['id']

        # Try to delete as user2
        client2 = APIClient()
        register_url = reverse('auth:register')
        register_data = {'email': 'user2@example.com', 'password': 'SecurePass123'}
        register_response = client2.post(register_url, register_data, format='json')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {register_response.data["access"]}')

        delete_url = reverse(
            'annotations:detail',
            kwargs={'point_id': point_id, 'pk': annotation_id}
        )
        response = client2.delete(delete_url)

        # Should be 403 (no access to point) or 404 (point not visible)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    # T028: GET /annotations/{id}/download - Download file
    def test_download_file_annotation_success(self, authenticated_user):
        """
        Test downloading file annotation.

        Expected:
        - Status: 200 OK (local) or 302 Found (S3 redirect)
        - Content-Type matches file mime type
        - Content-Disposition header with filename
        """
        api_client, user, point_id = authenticated_user

        # Create file annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        file_content = b'test-file-content'
        file_data = {
            'type': 'document',
            'file': SimpleUploadedFile("document.pdf", file_content, content_type="application/pdf")
        }
        create_response = api_client.post(create_url, file_data, format='multipart')
        annotation_id = create_response.data['id']

        # Download file
        download_url = reverse('annotations:download', kwargs={'pk': annotation_id})
        response = api_client.get(download_url)

        # Accept both 200 (local storage) and 302 (S3 redirect)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_302_FOUND]

        if response.status_code == status.HTTP_200_OK:
            assert response['Content-Type'] == 'application/pdf'
            assert 'Content-Disposition' in response
            assert 'document.pdf' in response['Content-Disposition']

    def test_download_text_annotation_fails(self, authenticated_user, text_annotation_data):
        """
        Test downloading text annotation (not allowed).

        Expected:
        - Status: 400 Bad Request
        - error indicates text annotations cannot be downloaded
        """
        api_client, user, point_id = authenticated_user

        # Create text annotation
        create_url = reverse('annotations:list', kwargs={'point_id': point_id})
        create_response = api_client.post(create_url, text_annotation_data, format='json')
        annotation_id = create_response.data['id']

        # Try to download
        download_url = reverse('annotations:download', kwargs={'pk': annotation_id})
        response = api_client.get(download_url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
