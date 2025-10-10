"""
Contract tests for Authentication API.

These tests validate the API contract defined in specs/001-build-a-web/contracts/auth.yaml
They MUST FAIL until views are implemented (TDD approach).

Tests cover:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login
- POST /api/v1/auth/refresh - Token refresh
- GET /api/v1/auth/me - Get current user profile
- POST /api/v1/auth/logout - Logout (client-side)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
@pytest.mark.contract
@pytest.mark.critical
class TestAuthenticationContract:
    """
    Contract tests for Authentication API endpoints.

    These tests validate request/response schemas match the OpenAPI spec.
    """

    @pytest.fixture
    def api_client(self):
        """Create API client for tests."""
        return APIClient()

    @pytest.fixture
    def valid_registration_data(self):
        """Valid user registration payload."""
        return {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }

    @pytest.fixture
    def valid_login_data(self):
        """Valid login credentials."""
        return {
            'email': 'test@example.com',
            'password': 'SecurePass123'
        }

    # T011: POST /auth/register - User registration
    def test_register_success(self, api_client, valid_registration_data):
        """
        Test successful user registration.

        Expected:
        - Status: 201 Created
        - Response contains: access, refresh, user
        - User has: id, email, date_joined, storage_used, storage_limit
        - Default storage_limit: 2GB (2147483648 bytes)
        - storage_used: 0 (new user)
        """
        url = reverse('auth:register')
        response = api_client.post(url, valid_registration_data, format='json')

        # Validate status code
        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

        # Validate user object
        user = response.data['user']
        assert 'id' in user
        assert user['email'] == valid_registration_data['email']
        assert 'date_joined' in user
        assert user['storage_used'] == 0
        assert user['storage_limit'] == 2 * 1024 * 1024 * 1024  # 2GB
        assert 'storage_percentage' in user
        assert user['storage_percentage'] == 0.0

    def test_register_duplicate_email(self, api_client, valid_registration_data):
        """
        Test registration with duplicate email.

        Expected:
        - Status: 400 Bad Request
        - Response contains: error, message, details
        - details.email: ["Email already registered"]
        """
        url = reverse('auth:register')

        # First registration
        api_client.post(url, valid_registration_data, format='json')

        # Duplicate registration
        response = api_client.post(url, valid_registration_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert response.data['error'] == 'VALIDATION_ERROR'
        assert 'message' in response.data
        assert 'details' in response.data
        assert 'email' in response.data['details']

    def test_register_weak_password(self, api_client):
        """
        Test registration with weak password.

        Expected:
        - Status: 400 Bad Request
        - details.password: contains validation error
        """
        url = reverse('auth:register')
        weak_data = {
            'email': 'weak@example.com',
            'password': 'weak'  # Too short, no uppercase, no numbers
        }

        response = api_client.post(url, weak_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'details' in response.data
        assert 'password' in response.data['details']

    # T012: POST /auth/login - User login
    def test_login_success(self, api_client, valid_registration_data, valid_login_data):
        """
        Test successful login.

        Expected:
        - Status: 200 OK
        - Response contains: access, refresh, user
        - Tokens are valid JWT strings
        """
        # Create user first
        register_url = reverse('auth:register')
        api_client.post(register_url, valid_registration_data, format='json')

        # Login
        login_url = reverse('auth:login')
        response = api_client.post(login_url, valid_login_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == valid_login_data['email']

    def test_login_invalid_credentials(self, api_client):
        """
        Test login with invalid credentials.

        Expected:
        - Status: 401 Unauthorized
        - error: INVALID_CREDENTIALS
        - message: "Email or password incorrect"
        """
        url = reverse('auth:login')
        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'WrongPass123'
        }

        response = api_client.post(url, invalid_data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error'] == 'INVALID_CREDENTIALS'
        assert 'message' in response.data

    # T013: POST /auth/refresh - Token refresh
    def test_refresh_token_success(self, api_client, valid_registration_data):
        """
        Test successful token refresh.

        Expected:
        - Status: 200 OK
        - Response contains: access (new access token)
        - New access token is different from original
        """
        # Register and get tokens
        register_url = reverse('auth:register')
        register_response = api_client.post(
            register_url,
            valid_registration_data,
            format='json'
        )
        refresh_token = register_response.data['refresh']
        original_access = register_response.data['access']

        # Refresh token
        refresh_url = reverse('auth:refresh')
        response = api_client.post(
            refresh_url,
            {'refresh': refresh_token},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert response.data['access'] != original_access

    def test_refresh_token_invalid(self, api_client):
        """
        Test refresh with invalid token.

        Expected:
        - Status: 401 Unauthorized
        - error: INVALID_TOKEN
        - message: "Refresh token expired or invalid"
        """
        url = reverse('auth:refresh')
        response = api_client.post(
            url,
            {'refresh': 'invalid-token'},
            format='json'
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error'] == 'INVALID_TOKEN'
        assert 'message' in response.data

    # T014: GET /auth/me - Get current user profile
    def test_get_current_user_success(self, api_client, valid_registration_data):
        """
        Test get current user profile.

        Expected:
        - Status: 200 OK
        - Response contains: id, email, date_joined, storage_used, storage_limit
        """
        # Register and get access token
        register_url = reverse('auth:register')
        register_response = api_client.post(
            register_url,
            valid_registration_data,
            format='json'
        )
        access_token = register_response.data['access']

        # Get profile
        url = reverse('auth:me')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'id' in response.data
        assert response.data['email'] == valid_registration_data['email']
        assert 'date_joined' in response.data
        assert 'storage_used' in response.data
        assert 'storage_limit' in response.data
        assert 'storage_percentage' in response.data

    def test_get_current_user_unauthorized(self, api_client):
        """
        Test get profile without authentication.

        Expected:
        - Status: 401 Unauthorized
        - error field present
        """
        url = reverse('auth:me')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # T015: POST /auth/logout - Logout
    def test_logout_success(self, api_client, valid_registration_data):
        """
        Test logout endpoint.

        Expected:
        - Status: 204 No Content
        - Empty response body

        Note: JWT logout is client-side (discard tokens).
        Server just acknowledges the request.
        """
        # Register and get access token
        register_url = reverse('auth:register')
        register_response = api_client.post(
            register_url,
            valid_registration_data,
            format='json'
        )
        access_token = register_response.data['access']

        # Logout
        url = reverse('auth:logout')
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data  # Empty response

    def test_logout_unauthorized(self, api_client):
        """
        Test logout without authentication.

        Expected:
        - Status: 401 Unauthorized
        """
        url = reverse('auth:logout')
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
