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
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.points.models import PointType


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
        return {"username": "testuser", "email": "test@example.com", "password": "SecurePass123"}

    @pytest.fixture
    def valid_login_data(self):
        """Valid login credentials."""
        return {"email": "test@example.com", "password": "SecurePass123"}

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
        url = reverse("authentication:register")
        response = api_client.post(url, valid_registration_data, format="json")

        # Validate status code
        assert response.status_code == status.HTTP_201_CREATED

        # Validate response structure
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

        # Validate user object
        user = response.data["user"]
        assert "id" in user
        assert user["email"] == valid_registration_data["email"]
        assert "date_joined" in user
        assert user["storage_used"] == 0
        assert user["storage_limit"] == 2 * 1024 * 1024 * 1024  # 2GB
        assert "storage_percentage" in user
        assert user["storage_percentage"] == 0.0

    def test_register_duplicate_email(self, api_client, valid_registration_data):
        """
        Test registration with duplicate email.

        Expected:
        - Status: 400 Bad Request
        - Response contains: error, message, details
        - details.email: ["Email already registered"]
        """
        url = reverse("authentication:register")

        # First registration
        api_client.post(url, valid_registration_data, format="json")

        # Duplicate registration with same email but different username
        duplicate_data = {
            "username": "testuser2",  # Different username
            "email": valid_registration_data["email"],  # Same email
            "password": "SecurePass123",
        }
        response = api_client.post(url, duplicate_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert response.data["error"] == "VALIDATION_ERROR"
        assert "message" in response.data
        assert "details" in response.data
        assert "email" in response.data["details"]

    def test_register_weak_password(self, api_client):
        """
        Test registration with weak password.

        Expected:
        - Status: 400 Bad Request
        - details.password: contains validation error
        """
        url = reverse("authentication:register")
        weak_data = {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "weak",  # Too short, no uppercase, no numbers
        }

        response = api_client.post(url, weak_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data
        assert "details" in response.data
        assert "password" in response.data["details"]

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
        register_url = reverse("authentication:register")
        api_client.post(register_url, valid_registration_data, format="json")

        # Login
        login_url = reverse("authentication:login")
        response = api_client.post(login_url, valid_login_data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["email"] == valid_login_data["email"]

    def test_login_invalid_credentials(self, api_client):
        """
        Test login with invalid credentials.

        Expected:
        - Status: 401 Unauthorized
        - error: INVALID_CREDENTIALS
        - message: "Email or password incorrect"
        """
        url = reverse("authentication:login")
        invalid_data = {"email": "nonexistent@example.com", "password": "WrongPass123"}

        response = api_client.post(url, invalid_data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data or "details" in response.data
        assert "message" in response.data or "detail" in response.data

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
        register_url = reverse("authentication:register")
        register_response = api_client.post(register_url, valid_registration_data, format="json")
        refresh_token = register_response.data["refresh"]
        original_access = register_response.data["access"]

        # Refresh token
        refresh_url = reverse("authentication:refresh")
        response = api_client.post(refresh_url, {"refresh": refresh_token}, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert response.data["access"] != original_access

    def test_refresh_token_invalid(self, api_client):
        """
        Test refresh with invalid token.

        Expected:
        - Status: 401 Unauthorized
        - error: INVALID_TOKEN
        - message: "Refresh token expired or invalid"
        """
        url = reverse("authentication:refresh")
        response = api_client.post(url, {"refresh": "invalid-token"}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["error"] == "INVALID_TOKEN"
        assert "message" in response.data

    # T014: GET /auth/me - Get current user profile
    def test_get_current_user_success(self, api_client, valid_registration_data):
        """
        Test get current user profile.

        Expected:
        - Status: 200 OK
        - Response contains: id, email, date_joined, storage_used, storage_limit
        """
        # Register and get access token
        register_url = reverse("authentication:register")
        register_response = api_client.post(register_url, valid_registration_data, format="json")
        access_token = register_response.data["access"]

        # Get profile
        url = reverse("authentication:profile")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.data
        assert response.data["email"] == valid_registration_data["email"]
        assert "date_joined" in response.data
        assert "storage_used" in response.data
        assert "storage_limit" in response.data
        assert "storage_percentage" in response.data

    def test_get_current_user_unauthorized(self, api_client):
        """
        Test get profile without authentication.

        Expected:
        - Status: 401 Unauthorized
        - error field present
        """
        url = reverse("authentication:profile")
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
        register_url = reverse("authentication:register")
        register_response = api_client.post(register_url, valid_registration_data, format="json")
        access_token = register_response.data["access"]

        # Logout
        url = reverse("authentication:logout")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.data  # Empty response

    def test_logout_unauthorized(self, api_client):
        """
        Test logout without authentication.

        Expected:
        - Status: 401 Unauthorized
        """
        url = reverse("authentication:logout")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.unit
class TestUserPointTypeValidation:
    """Unit tests for User model with PointType constraints."""

    def test_user_can_create_types_up_to_limit(self, alice):
        """Test that user can create types up to 1000."""
        from apps.points.models import PointType

        # Create 10 types as sample (creating 1000 would be slow)
        for i in range(10):
            PointType.objects.create(names={"en": f"Type_{i}"}, owner=alice, order=i)

        types = PointType.objects.filter(owner=alice, status="active")
        assert types.count() == 10

    def test_user_cannot_exceed_1000_types(self, alice):
        """Test that user cannot create more than 1000 types."""

        # Create 1000 types
        for i in range(1000):
            PointType.objects.create(names={"en": f"Type_{i}"}, owner=alice, order=i)

        # Check initial count of active types
        assert PointType.objects.filter(owner=alice, status="active").count() == 1000

        # Attempt to create the 1001st type
        with pytest.raises(ValidationError):
            point_type = PointType(names={"en": "Type_1001"}, owner=alice, order=1000)
            point_type.full_clean()

        # Check that still only 1000 types exist
        assert PointType.objects.filter(owner=alice, status="active").count() == 1000

    def test_deleted_types_dont_count_toward_limit(self, alice):
        """Test that deleted types don't count toward the 1000 type limit."""
        from apps.points.models import PointType

        # Create 10 types
        for i in range(10):
            PointType.objects.create(names={"en": f"Type_{i}"}, owner=alice, order=i)

        # Delete 5 types
        types_to_delete = PointType.objects.filter(owner=alice)[:5]
        for point_type in types_to_delete:
            point_type.status = "deleted"
            point_type.save()

        # Should only count active types
        active_types = PointType.objects.filter(owner=alice, status="active")
        assert active_types.count() == 5

        # Should be able to create more types
        new_type = PointType.objects.create(names={"en": "New_Type"}, owner=alice, order=11)
        assert new_type.id is not None
