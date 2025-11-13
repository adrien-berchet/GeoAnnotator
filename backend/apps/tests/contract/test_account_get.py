"""
Contract test: GET /api/account/

Test retrieving current authenticated user's account information.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAccountGetContract:
    """Contract tests for GET /api/account/ endpoint."""

    def test_get_account_returns_200_with_object(self, authenticated_client_alice):
        """
        Test that GET /api/account/ returns 200 with account object.

        Contract:
        - Status: 200 OK
        - Body: Account information object
        - Authentication: Required
        """
        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_get_account_response_schema(self, authenticated_client_alice):
        """
        Test that account object has the correct schema.

        Contract:
        - id: integer
        - username: string (required)
        - email: string (decrypted)
        - date_joined: datetime string
        - Does NOT include: password, deleted_at, pending_email
        """
        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check required fields are present
        assert "id" in response.data
        assert "email" in response.data
        assert "username" in response.data
        assert "date_joined" in response.data

        # Check username field is string (required now)
        assert isinstance(response.data["username"], str)

        # Check sensitive fields are excluded
        assert "password" not in response.data
        assert "deleted_at" not in response.data
        assert "pending_email" not in response.data

        # Check field types
        assert isinstance(response.data["id"], str)  # UUID as string
        assert isinstance(response.data["email"], str)
        assert isinstance(response.data["date_joined"], str)

    def test_get_account_requires_authentication(self, api_client):
        """
        Test that GET /api/account/ requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-retrieve")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "error" in response.data
        assert response.data["error"] == "UNAUTHORIZED"

    def test_get_account_shows_decrypted_email(self, authenticated_client_alice, alice):
        """
        Test that email is decrypted and shown to account owner.

        Contract:
        - Email field contains plain text email (not encrypted)
        """
        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == alice.email
        assert "@" in response.data["email"]  # Valid email format

    def test_get_account_with_username(self, authenticated_client_alice, alice):
        """Test that username is returned if set."""
        # Set username
        alice.username = "alice_wonderland"
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "alice_wonderland"

    def test_deleted_user_returns_404(self, authenticated_client_alice, alice):
        """
        Test that deleted users (deleted_at != NULL) return 404.

        Contract:
        - Soft-deleted users cannot access their account
        """
        from django.utils import timezone

        # Soft delete the user
        alice.deleted_at = timezone.now()
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        # Should return 404 or 401 (depending on implementation)
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
        ]
