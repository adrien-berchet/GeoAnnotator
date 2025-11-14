"""
Contract test: POST /api/account/validate-username/

Test username validation endpoint.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUsernameValidateContract:
    """Contract tests for POST /api/account/validate-username/ endpoint."""

    def test_validate_username_valid_available_returns_200(self, api_client):
        """
        Test that valid and available username returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "valid": true, "available": true }
        - Does not require authentication
        """
        url = reverse("authentication:username-validate")
        payload = {"username": "unique_username_123"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is True
        assert "error" not in response.data or response.data["error"] is None

    def test_validate_username_valid_taken_returns_200(self, api_client, alice):
        """
        Test that valid but taken username returns 200 with available=false.

        Contract:
        - Status: 200 OK
        - Body: { "valid": true, "available": false, "error": "..." }
        """
        # Set Alice's username
        alice.username = "alice_taken"
        alice.save()

        url = reverse("authentication:username-validate")
        payload = {"username": "alice_taken"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is False
        assert "error" in response.data
        assert "taken" in response.data["error"].lower()

    def test_validate_username_with_spaces_returns_200_invalid(self, api_client):
        """
        Test that username with spaces returns invalid.

        Contract:
        - Status: 200 OK
        - Body: { "valid": false, "available": null, "error": "..." }
        """
        url = reverse("authentication:username-validate")
        payload = {"username": "invalid username"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None
        assert "error" in response.data
        assert "space" in response.data["error"].lower()

    def test_validate_username_too_long_returns_200_invalid(self, api_client):
        """
        Test that username over 100 characters returns invalid.

        Contract:
        - Max length: 100 characters
        """
        url = reverse("authentication:username-validate")
        payload = {"username": "a" * 101}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None

    def test_validate_username_empty_returns_200_invalid(self, api_client):
        """
        Test that empty username returns invalid.

        Contract:
        - Minimum length: 3 characters
        """
        url = reverse("authentication:username-validate")
        payload = {"username": ""}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None

    def test_validate_username_case_insensitive_check(self, api_client, alice):
        """
        Test that uniqueness check is case-insensitive.

        Contract:
        - "Alice" and "alice" are considered duplicates
        """
        alice.username = "AliceWonderland"
        alice.save()

        url = reverse("authentication:username-validate")
        payload = {"username": "alicewonderland"}  # Different case
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is False

    def test_validate_username_special_characters_valid(self, api_client):
        """
        Test that username with underscores and hyphens is valid.

        Contract:
        - Allowed characters: letters, numbers, underscores, hyphens
        - Must start with alphanumeric
        """
        url = reverse("authentication:username-validate")
        payload = {"username": "user_2024"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is True

    def test_validate_username_does_not_require_authentication(self, api_client):
        """
        Test that validation works without authentication.

        Contract:
        - Optional authentication (can be used during registration)
        """
        url = reverse("authentication:username-validate")
        payload = {"username": "test_user"}
        response = api_client.post(url, payload, format="json")

        # Should work without authentication
        assert response.status_code == status.HTTP_200_OK
        assert "valid" in response.data

    def test_validate_username_does_not_create_records(self, api_client, alice):
        """
        Test that validation does not create or modify any records.

        Contract:
        - Read-only operation
        - No side effects
        """
        from apps.authentication.models import User

        initial_user_count = User.objects.count()

        url = reverse("authentication:username-validate")
        payload = {"username": "test_validate"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # No new users created
        assert User.objects.count() == initial_user_count

        # No user has this username
        assert not User.objects.filter(username="test_validate").exists()
