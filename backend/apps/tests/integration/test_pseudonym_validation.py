"""
Integration test: Pseudonym validation flow

Test the complete validation flow for pseudonyms (spaces, length, duplicates, special chars).
Matches quickstart scenario: Real-time validation as user types.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import User


@pytest.mark.django_db
class TestPseudonymValidationFlow:
    """Integration tests for pseudonym validation user journey."""

    def test_validation_endpoint_rejects_spaces(self, api_client):
        """
        Test validation endpoint rejects pseudonyms with spaces.

        Scenario: User types "my name" → Frontend calls validation → Shows error.
        """
        url = reverse("authentication:validate-pseudonym")

        response = api_client.post(url, {"pseudonym": "my name"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False
        assert response.data["available"] is None
        assert "space" in response.data["error"].lower()

    def test_validation_endpoint_rejects_too_long(self, api_client):
        """Test validation endpoint rejects pseudonyms over 99 characters."""
        url = reverse("authentication:validate-pseudonym")
        long_pseudonym = "a" * 100

        response = api_client.post(url, {"pseudonym": long_pseudonym}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False

    def test_validation_endpoint_accepts_99_chars(self, api_client):
        """Test validation endpoint accepts exactly 99 characters."""
        url = reverse("authentication:validate-pseudonym")
        pseudonym = "a" * 99

        response = api_client.post(url, {"pseudonym": pseudonym}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is True

    def test_validation_endpoint_detects_duplicate(self, api_client, user_alice):
        """
        Test validation endpoint detects duplicate pseudonyms.

        Scenario: User types "alice" → System checks → Already taken.
        """
        user_alice.pseudonym = "alice"
        user_alice.save()

        url = reverse("authentication:validate-pseudonym")
        response = api_client.post(url, {"pseudonym": "alice"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is True  # Format is valid
        assert response.data["available"] is False  # But taken
        assert "taken" in response.data["error"].lower()

    def test_validation_endpoint_case_insensitive_duplicate(self, api_client, user_alice):
        """Test validation detects duplicates case-insensitively."""
        user_alice.pseudonym = "AliceInWonderland"
        user_alice.save()

        url = reverse("authentication:validate-pseudonym")

        # Try lowercase
        response = api_client.post(url, {"pseudonym": "aliceinwonderland"}, format="json")
        assert response.data["available"] is False

        # Try uppercase
        response = api_client.post(url, {"pseudonym": "ALICEINWONDERLAND"}, format="json")
        assert response.data["available"] is False

    def test_validation_endpoint_allows_special_chars(self, api_client):
        """Test validation endpoint allows special characters (except spaces)."""
        url = reverse("authentication:validate-pseudonym")

        special_pseudonyms = ["user_123", "user-name", "user.name", "user@test", "user#123"]

        for pseudonym in special_pseudonyms:
            response = api_client.post(url, {"pseudonym": pseudonym}, format="json")
            assert response.status_code == 200
            assert response.data["valid"] is True, f"Failed for {pseudonym}"

    def test_update_endpoint_rejects_spaces(self, user_alice, authenticated_client_alice):
        """
        Test update endpoint rejects pseudonyms with spaces.

        Scenario: User submits form with "my name" → Backend rejects.
        """
        url = reverse("authentication:account-detail")

        response = authenticated_client_alice.patch(url, {"pseudonym": "my name"}, format="json")

        assert response.status_code == 400
        assert "pseudonym" in response.data

    def test_update_endpoint_rejects_too_long(self, user_alice, authenticated_client_alice):
        """Test update endpoint rejects pseudonyms over 99 characters."""
        url = reverse("authentication:account-detail")
        long_pseudonym = "a" * 100

        response = authenticated_client_alice.patch(
            url, {"pseudonym": long_pseudonym}, format="json"
        )

        assert response.status_code == 400

    def test_update_endpoint_rejects_duplicate(
        self, user_alice, user_bob, authenticated_client_alice
    ):
        """Test update endpoint rejects duplicate pseudonyms."""
        user_bob.pseudonym = "BobTheBest"
        user_bob.save()

        url = reverse("authentication:account-detail")

        response = authenticated_client_alice.patch(
            url,
            {"pseudonym": "BobTheBest"},
            format="json",  # Try to use Bob's pseudonym
        )

        assert response.status_code == 400
        assert "pseudonym" in response.data

    def test_full_validation_flow_invalid_to_valid(self, api_client):
        """
        Test complete flow from invalid to valid pseudonym.

        User journey:
        1. Types "my name" → Validation fails (spaces)
        2. Types "verylongnamethatiswaytoomanychars..." → Validation fails (length)
        3. Types "ValidName123" → Validation succeeds
        """
        url = reverse("authentication:validate-pseudonym")

        # Step 1: Try with spaces
        response = api_client.post(url, {"pseudonym": "my name"}, format="json")
        assert response.data["valid"] is False

        # Step 2: Try too long
        response = api_client.post(url, {"pseudonym": "a" * 100}, format="json")
        assert response.data["valid"] is False

        # Step 3: Valid format
        response = api_client.post(url, {"pseudonym": "ValidName123"}, format="json")
        assert response.data["valid"] is True
        assert response.data["available"] is True

    def test_full_validation_and_update_flow(self, api_client):
        """
        Test complete flow from validation to successful update.

        User journey:
        1. Validate pseudonym → Returns valid + available
        2. Submit update → Succeeds
        3. Validate same pseudonym again → Now taken
        """
        # Create and login user
        user = User.objects.create_user(
            email="flowtest@example.com", password="Pass123!", pseudonym=""
        )
        api_client.force_authenticate(user=user)

        validate_url = reverse("authentication:validate-pseudonym")
        update_url = reverse("authentication:account-detail")

        # Step 1: Validate
        response = api_client.post(validate_url, {"pseudonym": "FlowTest123"}, format="json")
        assert response.data["valid"] is True
        assert response.data["available"] is True

        # Step 2: Update
        response = api_client.patch(update_url, {"pseudonym": "FlowTest123"}, format="json")
        assert response.status_code == 200

        # Step 3: Validate again (now taken)
        response = api_client.post(validate_url, {"pseudonym": "FlowTest123"}, format="json")
        assert response.data["available"] is False

    def test_validation_empty_pseudonym(self, api_client):
        """Test validation endpoint handles empty pseudonym."""
        url = reverse("authentication:validate-pseudonym")

        response = api_client.post(url, {"pseudonym": ""}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False

    def test_validation_single_char_allowed(self, api_client):
        """Test validation allows single character pseudonyms."""
        url = reverse("authentication:validate-pseudonym")

        response = api_client.post(url, {"pseudonym": "a"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is True
