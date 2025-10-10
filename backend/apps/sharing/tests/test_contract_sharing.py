"""
Contract tests for Sharing API.

These tests validate the API contract defined in specs/001-build-a-web/contracts/sharing.yaml
They MUST FAIL until views are implemented (TDD approach).

Tests cover:
- POST /api/v1/points/{id}/shares - Create share invitation
- GET /api/v1/points/{id}/shares - List point's shares
- GET /api/v1/shares/{id} - Get share details
- PATCH /api/v1/shares/{id} - Update permission level
- DELETE /api/v1/shares/{id} - Revoke share
- POST /api/v1/shares/accept/{token} - Accept invitation
- GET /api/v1/shares/received - List received shares
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.contract
@pytest.mark.critical
class TestSharingContract:
    """
    Contract tests for Sharing API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def owner_with_point(self, api_client):
        """Create owner user with a GPS point."""
        # Register owner
        register_url = reverse('authentication:register')
        register_data = {
            'email': 'owner@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        access_token = response.data['access']
        user = response.data['user']

        # Set authentication
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create GPS point
        point_url = reverse('points:list')
        point_data = {
            'title': 'Shared Point',
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        point_response = api_client.post(point_url, point_data, format='json')
        point_id = point_response.data['id']

        return api_client, user, point_id

    @pytest.fixture
    def recipient_user(self, api_client):
        """Create recipient user."""
        # Save current credentials
        current_auth = api_client._credentials.copy() if hasattr(api_client, '_credentials') else {}

        # Temporarily clear authentication
        api_client.credentials()

        # Register recipient
        register_url = reverse('auth:register')
        register_data = {
            'email': 'recipient@example.com',
            'password': 'SecurePass123'
        }
        response = api_client.post(register_url, register_data, format='json')
        recipient = {
            'user': response.data['user'],
            'token': response.data['access']
        }

        # Restore original credentials
        if current_auth:
            api_client.credentials(**current_auth)

        return recipient

    # T029: POST /points/{id}/shares - Create share invitation
    def test_create_share_success(self, owner_with_point, recipient_user):
        """
        Test successful share creation.

        Expected:
        - Status: 201 Created
        - Response contains: id, gps_point, owner, recipient_email, permission_level
        - invitation_status is 'pending'
        - invitation_sent_at is set
        - is_active is true
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        response = api_client.post(url, share_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        share = response.data
        assert 'id' in share
        assert share['gps_point']['id'] == point_id
        assert share['owner']['id'] == owner['id']
        assert share['recipient_email'] == recipient['user']['email']
        assert share['permission_level'] == 'view'
        assert share['invitation_status'] == 'pending'
        assert 'invitation_sent_at' in share
        assert share['is_active'] is True
        assert 'created_at' in share

    def test_create_share_duplicate(self, owner_with_point, recipient_user):
        """
        Test creating duplicate share.

        Expected:
        - Status: 400 Bad Request
        - error: DUPLICATE_SHARE
        - details contains recipient_email
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }

        # Create first share
        api_client.post(url, share_data, format='json')

        # Try to create duplicate
        response = api_client.post(url, share_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'VALIDATION_ERROR'
        assert response.data["details"]['error'][0] == 'DUPLICATE_SHARE'

    def test_create_share_with_self(self, owner_with_point):
        """
        Test sharing with self.

        Expected:
        - Status: 400 Bad Request
        - error: INVALID_RECIPIENT
        - message indicates cannot share with yourself
        """
        api_client, owner, point_id = owner_with_point

        url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': owner['email'],
            'permission_level': 'view'
        }
        response = api_client.post(url, share_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['error'] == 'VALIDATION_ERROR'
        assert response.data["details"]['error'][0] == 'SELF_SHARE'

    # T030: GET /points/{id}/shares - List point's shares
    def test_list_shares_success(self, owner_with_point, recipient_user):
        """
        Test listing point's shares (owner only).

        Expected:
        - Status: 200 OK
        - Response is array of Share objects
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'edit'
        }
        api_client.post(create_url, share_data, format='json')

        # List shares
        list_url = reverse('sharing:list', kwargs={'point_id': point_id})
        response = api_client.get(list_url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

        # Validate share structure
        share = response.data[0]
        assert 'id' in share
        assert 'gps_point' in share
        assert 'recipient_email' in share
        assert 'permission_level' in share
        assert 'invitation_status' in share

    def test_list_shares_forbidden(self, api_client, owner_with_point, recipient_user):
        """
        Test listing shares as non-owner.

        Expected:
        - Status: 403 Forbidden
        - error: ACCESS_DENIED
        """
        _, owner, point_id = owner_with_point
        recipient = recipient_user

        # Try to list as recipient (not owner)
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        list_url = reverse('sharing:list', kwargs={'point_id': point_id})
        response = client2.get(list_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # T031: GET /shares/{id} - Get share details
    def test_get_share_success(self, owner_with_point, recipient_user):
        """
        Test getting share details.

        Expected:
        - Status: 200 OK
        - Full share details returned
        - Accessible by owner or recipient
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = api_client.post(create_url, share_data, format='json')
        share_id = create_response.data['id']

        # Get share details
        detail_url = reverse('global_sharing:detail', kwargs={'pk': share_id})
        response = api_client.get(detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == share_id

    # T032: PATCH /shares/{id} - Update permission level
    def test_update_share_permission_success(self, owner_with_point, recipient_user):
        """
        Test updating share permission level.

        Expected:
        - Status: 200 OK
        - permission_level is updated
        - Only owner can update
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share with view permission
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = api_client.post(create_url, share_data, format='json')
        share_id = create_response.data['id']

        # Update to edit permission
        update_url = reverse('global_sharing:detail', kwargs={'pk': share_id})
        update_data = {'permission_level': 'edit'}
        response = api_client.patch(update_url, update_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['permission_level'] == 'edit'

    def test_update_share_permission_forbidden(self, api_client, owner_with_point, recipient_user):
        """
        Test updating share permission as non-owner.

        Expected:
        - Status: 403 Forbidden
        """
        owner_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = owner_client.post(create_url, share_data, format='json')
        share_id = create_response.data['id']

        # Try to update as recipient
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        update_url = reverse('global_sharing:detail', kwargs={'pk': share_id})
        update_data = {'permission_level': 'transfer'}
        response = client2.patch(update_url, update_data, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # T033: DELETE /shares/{id} - Revoke share
    def test_revoke_share_success(self, owner_with_point, recipient_user):
        """
        Test revoking share.

        Expected:
        - Status: 204 No Content
        - Share is permanently deleted
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = api_client.post(create_url, share_data, format='json')
        share_id = create_response.data['id']

        # Revoke share
        delete_url = reverse('global_sharing:detail', kwargs={'pk': share_id})
        response = api_client.delete(delete_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion
        get_response = api_client.get(delete_url)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_revoke_share_forbidden(self, api_client, owner_with_point, recipient_user):
        """
        Test revoking share as non-owner.

        Expected:
        - Status: 403 Forbidden
        """
        owner_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = owner_client.post(create_url, share_data, format='json')
        share_id = create_response.data['id']

        # Try to revoke as recipient
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        delete_url = reverse('global_sharing:detail', kwargs={'pk': share_id})
        response = client2.delete(delete_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    # T034: POST /shares/accept/{token} - Accept invitation
    def test_accept_share_success(self, owner_with_point, recipient_user):
        """
        Test accepting share invitation.

        Expected:
        - Status: 200 OK
        - invitation_status changes to 'accepted'
        - accepted_at is set
        - recipient_user is linked
        """
        api_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        create_response = api_client.post(create_url, share_data, format='json')
        invitation_token = create_response.data['invitation_token']

        # Accept invitation using the proper invitation_token
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        accept_url = reverse('global_sharing:accept', kwargs={'token': invitation_token})
        response = client2.post(accept_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['invitation_status'] == 'accepted'
        assert 'accepted_at' in response.data
        assert response.data['accepted_at'] is not None

    # T035: GET /shares/received - List received shares
    def test_list_received_shares_success(self, owner_with_point, recipient_user):
        """
        Test listing received shares.

        Expected:
        - Status: 200 OK
        - Response is array of shares received by current user
        """
        owner_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'edit'
        }
        owner_client.post(create_url, share_data, format='json')

        # List received shares as recipient
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        received_url = reverse('global_sharing:received')
        response = client2.get(received_url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 1

        # Validate share structure
        share = response.data[0]
        assert share['recipient_email'] == recipient['user']['email']
        assert 'permission_level' in share

    def test_list_received_shares_with_status_filter(self, owner_with_point, recipient_user):
        """
        Test listing received shares with status filter.

        Expected:
        - Only shares matching status are returned
        """
        owner_client, owner, point_id = owner_with_point
        recipient = recipient_user

        # Create share
        create_url = reverse('sharing:list', kwargs={'point_id': point_id})
        share_data = {
            'recipient_email': recipient['user']['email'],
            'permission_level': 'view'
        }
        owner_client.post(create_url, share_data, format='json')

        # List pending shares as recipient
        client2 = APIClient()
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {recipient["token"]}')

        received_url = reverse('global_sharing:received')
        response = client2.get(received_url, {'status': 'pending'})

        assert response.status_code == status.HTTP_200_OK
        assert all(share['invitation_status'] == 'pending' for share in response.data)
