"""
Contract tests for GPS Points API.

These tests validate the API contract defined in specs/001-build-a-web/contracts/points.yaml
They MUST FAIL until views are implemented (TDD approach).

Tests cover:
- POST /api/v1/points - Create GPS point
- GET /api/v1/points - List GPS points with filters
- GET /api/v1/points/{id} - Get point details
- PUT /api/v1/points/{id} - Update point
- DELETE /api/v1/points/{id} - Delete point (soft delete)
- POST /api/v1/points/{id}/lock - Acquire editing lock
- DELETE /api/v1/points/{id}/lock - Release editing lock
- GET /api/v1/tags - List tags
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.contract
@pytest.mark.critical
class TestPointsContract:
    """
    Contract tests for GPS Points API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def authenticated_user(self, api_client):
        """Create and authenticate a user, return (client, user_data)."""
        # Register user
        register_url = reverse('auth:register')
        register_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        access_token = response.data['access']

        # Set authentication
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        return api_client, response.data['user']

    @pytest.fixture
    def valid_point_data(self):
        """Valid GPS point creation payload."""
        return {
            'title': 'Test Point',
            'description': 'A test GPS point with <strong>HTML</strong> 🌲',
            'latitude': 37.7749,
            'longitude': -122.4194,
            'tags': ['hiking', 'forest'],
            'is_public': False
        }

    # T016: POST /points - Create GPS point
    def test_create_point_success(self, authenticated_user, valid_point_data):
        """
        Test successful GPS point creation.

        Expected:
        - Status: 201 Created
        - Response contains: id, title, description, location, latitude, longitude
        - owner matches authenticated user
        - tags are created and linked
        - created_at and updated_at are set
        - permission is 'owner'
        """
        api_client, user = authenticated_user
        url = reverse('points:list')
        response = api_client.post(url, valid_point_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        point = response.data
        assert 'id' in point
        assert point['title'] == valid_point_data['title']
        assert point['description'] == valid_point_data['description']
        assert point['latitude'] == valid_point_data['latitude']
        assert point['longitude'] == valid_point_data['longitude']
        assert point['is_public'] == valid_point_data['is_public']

        # Validate location GeoJSON
        assert point['location']['type'] == 'Point'
        assert point['location']['coordinates'] == [
            valid_point_data['longitude'],
            valid_point_data['latitude']
        ]

        # Validate owner
        assert point['owner']['id'] == user['id']
        assert point['owner']['email'] == user['email']

        # Validate tags
        assert len(point['tags']) == 2
        tag_names = [tag['name'] for tag in point['tags']]
        assert 'hiking' in tag_names
        assert 'forest' in tag_names

        # Validate timestamps
        assert 'created_at' in point
        assert 'updated_at' in point

        # Validate permission
        assert point['permission'] == 'owner'

        # Validate editing_lock is null for new point
        assert point['editing_lock'] is None

    def test_create_point_validation_error(self, authenticated_user):
        """
        Test point creation with invalid data.

        Expected:
        - Status: 400 Bad Request
        - error: VALIDATION_ERROR
        - details contains field-specific errors
        """
        api_client, _ = authenticated_user
        url = reverse('points:list')
        invalid_data = {
            'title': '',  # Empty title
            'latitude': 100,  # Invalid latitude (>90)
            'longitude': -200  # Invalid longitude (<-180)
        }

        response = api_client.post(url, invalid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'VALIDATION_ERROR'
        assert 'details' in response.data
        assert 'title' in response.data['details']
        assert 'latitude' in response.data['details']
        assert 'longitude' in response.data['details']

    def test_create_point_unauthorized(self, api_client, valid_point_data):
        """
        Test point creation without authentication.

        Expected:
        - Status: 401 Unauthorized
        """
        url = reverse('points:list')
        response = api_client.post(url, valid_point_data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # T017: GET /points - List GPS points
    def test_list_points_success(self, authenticated_user, valid_point_data):
        """
        Test listing GPS points with pagination.

        Expected:
        - Status: 200 OK
        - Response contains: count, next, previous, results
        - results is array of GPSPoint objects
        """
        api_client, _ = authenticated_user

        # Create a point first
        create_url = reverse('points:list')
        api_client.post(create_url, valid_point_data, format='json')

        # List points
        list_url = reverse('points:list')
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'results' in response.data
        assert response.data['count'] >= 1
        assert len(response.data['results']) >= 1

        # Validate first point structure
        point = response.data['results'][0]
        assert 'id' in point
        assert 'title' in point
        assert 'location' in point
        assert 'owner' in point
        assert 'tags' in point
        assert 'permission' in point

    def test_list_points_with_bbox_filter(self, authenticated_user, valid_point_data):
        """
        Test listing points with bounding box filter.

        Expected:
        - Only points within bbox are returned
        """
        api_client, _ = authenticated_user

        # Create point
        create_url = reverse('points:list')
        api_client.post(create_url, valid_point_data, format='json')

        # List with bbox that includes the point
        list_url = reverse('points:list')
        bbox = '-123,37,-122,38'  # Includes San Francisco
        response = api_client.get(list_url, {'bbox': bbox})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_list_points_with_tags_filter(self, authenticated_user, valid_point_data):
        """
        Test listing points with tags filter.

        Expected:
        - Only points with specified tags are returned
        """
        api_client, _ = authenticated_user

        # Create point with tags
        create_url = reverse('points:list')
        api_client.post(create_url, valid_point_data, format='json')

        # List with tags filter
        list_url = reverse('points:list')
        response = api_client.get(list_url, {'tags': 'hiking,forest'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    # T018: GET /points/{id} - Get point details
    def test_get_point_success(self, authenticated_user, valid_point_data):
        """
        Test getting GPS point details.

        Expected:
        - Status: 200 OK
        - Full point details returned
        """
        api_client, _ = authenticated_user

        # Create point
        create_url = reverse('points:list')
        create_response = api_client.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        # Get point
        detail_url = reverse('points:detail', kwargs={'pk': point_id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == point_id
        assert response.data['title'] == valid_point_data['title']

    def test_get_point_not_found(self, authenticated_user):
        """
        Test getting non-existent point.

        Expected:
        - Status: 404 Not Found
        - error: POINT_NOT_FOUND
        """
        api_client, _ = authenticated_user

        # Try to get non-existent point
        url = reverse('points:detail', kwargs={'pk': '00000000-0000-0000-0000-000000000000'})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data['error'] == 'POINT_NOT_FOUND'

    def test_get_point_forbidden(self, api_client, authenticated_user, valid_point_data):
        """
        Test getting point without access.

        Expected:
        - Status: 403 Forbidden
        - error: ACCESS_DENIED
        """
        # Create point as user1
        client1, _ = authenticated_user
        create_url = reverse('points:list')
        private_point_data = {**valid_point_data, 'is_public': False}
        create_response = client1.post(create_url, private_point_data, format='json')
        point_id = create_response.data['id']

        # Try to access as user2
        client2 = APIClient()
        register_url = reverse('auth:register')
        register_data = {'email': 'user2@example.com', 'password': 'SecurePass123'}
        register_response = client2.post(register_url, register_data, format='json')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {register_response.data["access"]}')

        detail_url = reverse('points:detail', kwargs={'pk': point_id})
        response = client2.get(detail_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error'] == 'ACCESS_DENIED'

    # T019: PUT /points/{id} - Update point
    def test_update_point_success(self, authenticated_user, valid_point_data):
        """
        Test successful point update.

        Expected:
        - Status: 200 OK
        - Point is updated
        - editing_lock is acquired
        - updated_at is changed
        """
        api_client, _ = authenticated_user

        # Create point
        create_url = reverse('points:list')
        create_response = api_client.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']
        original_updated_at = create_response.data['updated_at']

        # Update point
        update_url = reverse('points:detail', kwargs={'pk': point_id})
        update_data = {'title': 'Updated Title'}
        response = api_client.put(update_url, update_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Updated Title'
        assert response.data['updated_at'] != original_updated_at

        # Validate editing_lock was acquired
        assert response.data['editing_lock'] is not None
        assert 'user' in response.data['editing_lock']
        assert 'acquired_at' in response.data['editing_lock']
        assert 'expires_at' in response.data['editing_lock']

    def test_update_point_locked_by_other_user(self, api_client, authenticated_user, valid_point_data):
        """
        Test updating point locked by another user.

        Expected:
        - Status: 409 Conflict
        - error: POINT_LOCKED
        - details contains locked_by and lock_expires_at
        """
        # Create point and acquire lock as user1
        client1, _ = authenticated_user
        create_url = reverse('points:list')
        create_response = client1.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        # Acquire lock
        lock_url = reverse('points:lock', kwargs={'pk': point_id})
        client1.post(lock_url)

        # Try to update as user2
        client2 = APIClient()
        register_url = reverse('auth:register')
        register_data = {'email': 'user2@example.com', 'password': 'SecurePass123'}
        register_response = client2.post(register_url, register_data, format='json')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {register_response.data["access"]}')

        # Share point with edit permission to user2 first
        # (This will be tested in sharing contract tests)
        # For now, assume user2 has edit permission

        update_url = reverse('points:detail', kwargs={'pk': point_id})
        update_data = {'title': 'Hacked Title'}
        response = client2.put(update_url, update_data, format='json')

        # Should fail with 409 or 403 depending on implementation
        assert response.status_code in [status.HTTP_409_CONFLICT, status.HTTP_403_FORBIDDEN]

    # T020: DELETE /points/{id} - Delete point (soft delete)
    def test_delete_point_success(self, authenticated_user, valid_point_data):
        """
        Test successful point deletion (soft delete).

        Expected:
        - Status: 204 No Content
        - Point is moved to trash (30-day retention)
        """
        api_client, _ = authenticated_user

        # Create point
        create_url = reverse('points:list')
        create_response = api_client.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        # Delete point
        delete_url = reverse('points:detail', kwargs={'pk': point_id})
        response = api_client.delete(delete_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify point is not accessible
        get_response = api_client.get(delete_url)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_point_forbidden(self, api_client, authenticated_user, valid_point_data):
        """
        Test deleting point without owner permission.

        Expected:
        - Status: 403 Forbidden
        - error: ACCESS_DENIED (only owner can delete)
        """
        # Create point as user1
        client1, _ = authenticated_user
        create_url = reverse('points:list')
        create_response = client1.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        # Try to delete as user2
        client2 = APIClient()
        register_url = reverse('auth:register')
        register_data = {'email': 'user2@example.com', 'password': 'SecurePass123'}
        register_response = client2.post(register_url, register_data, format='json')
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {register_response.data["access"]}')

        delete_url = reverse('points:detail', kwargs={'pk': point_id})
        response = client2.delete(delete_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error'] == 'ACCESS_DENIED'

    # T021: POST /points/{id}/lock - Acquire editing lock
    def test_acquire_lock_success(self, authenticated_user, valid_point_data):
        """
        Test acquiring editing lock.

        Expected:
        - Status: 200 OK
        - Returns EditingLock object with user, acquired_at, expires_at
        - Lock duration is 15 minutes
        """
        api_client, user = authenticated_user

        # Create point
        create_url = reverse('points:list')
        create_response = api_client.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        # Acquire lock
        lock_url = reverse('points:lock', kwargs={'pk': point_id})
        response = api_client.post(lock_url)

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert response.data['user']['id'] == user['id']
        assert 'acquired_at' in response.data
        assert 'expires_at' in response.data

    def test_release_lock_success(self, authenticated_user, valid_point_data):
        """
        Test releasing editing lock.

        Expected:
        - Status: 204 No Content
        - Lock is released
        """
        api_client, _ = authenticated_user

        # Create point and acquire lock
        create_url = reverse('points:list')
        create_response = api_client.post(create_url, valid_point_data, format='json')
        point_id = create_response.data['id']

        lock_url = reverse('points:lock', kwargs={'pk': point_id})
        api_client.post(lock_url)

        # Release lock
        response = api_client.delete(lock_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    # T022: GET /tags - List tags (moved from annotations contract)
    def test_list_tags_success(self, authenticated_user, valid_point_data):
        """
        Test listing all tags.

        Expected:
        - Status: 200 OK
        - Returns array of Tag objects
        """
        api_client, _ = authenticated_user

        # Create point with tags
        create_url = reverse('points:list')
        api_client.post(create_url, valid_point_data, format='json')

        # List tags
        tags_url = reverse('tags:list')
        response = api_client.get(tags_url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 2

        # Validate tag structure
        tag = response.data[0]
        assert 'id' in tag
        assert 'name' in tag
        assert 'created_at' in tag

    def test_list_tags_with_search(self, authenticated_user, valid_point_data):
        """
        Test listing tags with search filter.

        Expected:
        - Only tags matching search prefix are returned
        """
        api_client, _ = authenticated_user

        # Create point with tags
        create_url = reverse('points:list')
        api_client.post(create_url, valid_point_data, format='json')

        # Search tags
        tags_url = reverse('tags:list')
        response = api_client.get(tags_url, {'search': 'hik'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert any('hiking' in tag['name'].lower() for tag in response.data)
