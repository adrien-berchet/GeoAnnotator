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
        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_get_account_response_schema(self, authenticated_client_alice):
        """
        Test that account object has the correct schema.

        Contract:
        - id: integer
        - pseudonym: string or null
        - email: string (decrypted)
        - created_at: datetime string
        - updated_at: datetime string
        - Does NOT include: password, deleted_at, pending_email
        """
        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check required fields are present
        assert "id" in response.data
        assert "email" in response.data
        assert "created_at" in response.data
        assert "updated_at" in response.data

        # Check pseudonym field (can be null or string)
        assert "pseudonym" in response.data
        assert response.data["pseudonym"] is None or isinstance(response.data["pseudonym"], str)

        # Check sensitive fields are excluded
        assert "password" not in response.data
        assert "deleted_at" not in response.data
        assert "pending_email" not in response.data

        # Check field types
        assert isinstance(response.data["id"], int)
        assert isinstance(response.data["email"], str)
        assert isinstance(response.data["created_at"], str)
        assert isinstance(response.data["updated_at"], str)

    def test_get_account_requires_authentication(self, api_client):
        """
        Test that GET /api/account/ requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-detail")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.data

    def test_get_account_shows_decrypted_email(self, authenticated_client_alice, user_alice):
        """
        Test that email is decrypted and shown to account owner.

        Contract:
        - Email field contains plain text email (not encrypted)
        """
        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == user_alice.email
        assert "@" in response.data["email"]  # Valid email format

    def test_get_account_with_pseudonym(self, authenticated_client_alice, user_alice):
        """Test that pseudonym is returned if set."""
        # Set pseudonym
        user_alice.pseudonym = "alice_wonderland"
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["pseudonym"] == "alice_wonderland"

    def test_deleted_user_returns_404(self, authenticated_client_alice, user_alice):
        """
        Test that deleted users (deleted_at != NULL) return 404.

        Contract:
        - Soft-deleted users cannot access their account
        """
        from django.utils import timezone

        # Soft delete the user
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        # Should return 404 or 401 (depending on implementation)
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED,
        ]
