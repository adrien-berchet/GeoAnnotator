"""
Contract test: POST /api/account/validate-pseudonym/

Test pseudonym validation endpoint.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestPseudonymValidateContract:
    """Contract tests for POST /api/account/validate-pseudonym/ endpoint."""

    def test_validate_pseudonym_valid_available_returns_200(self, api_client):
        """
        Test that valid and available pseudonym returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "valid": true, "available": true }
        - Does not require authentication
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "unique_pseudonym_123"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is True
        assert "error" not in response.data or response.data["error"] is None

    def test_validate_pseudonym_valid_taken_returns_200(self, api_client, user_alice):
        """
        Test that valid but taken pseudonym returns 200 with available=false.

        Contract:
        - Status: 200 OK
        - Body: { "valid": true, "available": false, "error": "..." }
        """
        # Set Alice's pseudonym
        user_alice.pseudonym = "alice_taken"
        user_alice.save()

        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "alice_taken"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is False
        assert "error" in response.data
        assert "taken" in response.data["error"].lower()

    def test_validate_pseudonym_with_spaces_returns_200_invalid(self, api_client):
        """
        Test that pseudonym with spaces returns invalid.

        Contract:
        - Status: 200 OK
        - Body: { "valid": false, "available": null, "error": "..." }
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "invalid pseudo"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None
        assert "error" in response.data
        assert "space" in response.data["error"].lower()

    def test_validate_pseudonym_too_long_returns_200_invalid(self, api_client):
        """
        Test that pseudonym over 99 characters returns invalid.

        Contract:
        - Max length: 99 characters
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "a" * 100}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None

    def test_validate_pseudonym_empty_returns_200_invalid(self, api_client):
        """
        Test that empty pseudonym returns invalid.

        Contract:
        - Minimum length: 1 character
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": ""}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is False
        assert response.data["available"] is None

    def test_validate_pseudonym_case_insensitive_check(self, api_client, user_alice):
        """
        Test that uniqueness check is case-insensitive.

        Contract:
        - "Alice" and "alice" are considered duplicates
        """
        user_alice.pseudonym = "AliceWonderland"
        user_alice.save()

        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "alicewonderland"}  # Different case
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is False

    def test_validate_pseudonym_special_characters_valid(self, api_client):
        """
        Test that pseudonym with special characters is valid.

        Contract:
        - Special characters allowed (except spaces)
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "user_2024!@#"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["available"] is True

    def test_validate_pseudonym_does_not_require_authentication(self, api_client):
        """
        Test that validation works without authentication.

        Contract:
        - Optional authentication (can be used during registration)
        """
        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "test_user"}
        response = api_client.post(url, payload, format="json")

        # Should work without authentication
        assert response.status_code == status.HTTP_200_OK
        assert "valid" in response.data

    def test_validate_pseudonym_does_not_create_records(self, api_client, user_alice):
        """
        Test that validation does not create or modify any records.

        Contract:
        - Read-only operation
        - No side effects
        """
        from apps.authentication.models import User

        initial_user_count = User.objects.count()

        url = reverse("authentication:account-validate-pseudonym")
        payload = {"pseudonym": "test_validate"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # No new users created
        assert User.objects.count() == initial_user_count

        # No user has this pseudonym
        assert not User.objects.filter(pseudonym="test_validate").exists()
