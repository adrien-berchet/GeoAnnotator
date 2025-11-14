"""
Integration test: Username validation flow

Test the complete validation flow for usernames (spaces, length, duplicates, special chars).
Matches quickstart scenario: Real-time validation as user types.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import User


@pytest.mark.django_db
class TestUsernameValidationFlow:
    """Integration tests for username validation user journey."""

    def test_validation_endpoint_rejects_spaces(self, api_client):
        """
        Test validation endpoint rejects usernames with spaces.

        Scenario: User types "my name" → Frontend calls validation → Shows error.
        """
        url = reverse("authentication:username-validate")

        response = api_client.post(url, {"username": "my name"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False
        assert response.data["available"] is None
        assert "space" in response.data["error"].lower()

    def test_validation_endpoint_rejects_too_long(self, api_client):
        """Test validation endpoint rejects usernames over 100 characters."""
        url = reverse("authentication:username-validate")
        long_username = "a" * 101

        response = api_client.post(url, {"username": long_username}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False

    def test_validation_endpoint_accepts_100_chars(self, api_client):
        """Test validation endpoint accepts exactly 100 characters."""
        url = reverse("authentication:username-validate")
        username = "a" * 100

        response = api_client.post(url, {"username": username}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is True

    def test_validation_endpoint_detects_duplicate(self, api_client, alice):
        """
        Test validation endpoint detects duplicate usernames.

        Scenario: User types "alice" → System checks → Already taken.
        """
        alice.username = "alice"
        alice.save()

        url = reverse("authentication:username-validate")
        response = api_client.post(url, {"username": "alice"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is True  # Format is valid
        assert response.data["available"] is False  # But taken
        assert "taken" in response.data["error"].lower()

    def test_validation_endpoint_case_insensitive_duplicate(self, api_client, alice):
        """Test validation detects duplicates case-insensitively."""
        alice.username = "AliceInWonderland"
        alice.save()

        url = reverse("authentication:username-validate")

        # Try lowercase
        response = api_client.post(url, {"username": "aliceinwonderland"}, format="json")
        assert response.data["available"] is False

        # Try uppercase
        response = api_client.post(url, {"username": "ALICEINWONDERLAND"}, format="json")
        assert response.data["available"] is False

    def test_validation_endpoint_allows_special_chars(self, api_client):
        """Test validation endpoint allows underscores and hyphens."""
        url = reverse("authentication:username-validate")

        special_usernames = ["user_123", "user-name", "user_with-both"]

        for username in special_usernames:
            response = api_client.post(url, {"username": username}, format="json")
            assert response.status_code == 200
            assert response.data["valid"] is True, f"Failed for {username}"

    def test_update_endpoint_rejects_spaces(self, alice, authenticated_client_alice):
        """
        Test update endpoint rejects usernames with spaces.

        Scenario: User submits form with "my name" → Backend rejects.
        """
        url = reverse("authentication:account-update")

        response = authenticated_client_alice.patch(url, {"username": "my name"}, format="json")

        assert response.status_code == 400
        assert "details" in response.data
        assert "username" in response.data["details"]

    def test_update_endpoint_rejects_too_long(self, alice, authenticated_client_alice):
        """Test update endpoint rejects usernames over 100 characters."""
        url = reverse("authentication:account-update")
        long_username = "a" * 101

        response = authenticated_client_alice.patch(url, {"username": long_username}, format="json")

        assert response.status_code == 400

    def test_update_endpoint_rejects_duplicate(self, alice, bob, authenticated_client_alice):
        """Test update endpoint rejects duplicate usernames."""
        bob.username = "BobTheBest"
        bob.save()

        url = reverse("authentication:account-update")

        response = authenticated_client_alice.patch(
            url,
            {"username": "BobTheBest"},
            format="json",  # Try to use Bob's username
        )

        assert response.status_code == 400
        assert "details" in response.data
        assert "username" in response.data["details"]

    def test_full_validation_flow_invalid_to_valid(self, api_client):
        """
        Test complete flow from invalid to valid username.

        User journey:
        1. Types "my name" → Validation fails (spaces)
        2. Types "verylongnamethatiswaytoomanychars..." → Validation fails (length)
        3. Types "ValidName123" → Validation succeeds
        """
        url = reverse("authentication:username-validate")

        # Step 1: Try with spaces
        response = api_client.post(url, {"username": "my name"}, format="json")
        assert response.data["valid"] is False

        # Step 2: Try too long
        response = api_client.post(url, {"username": "a" * 101}, format="json")
        assert response.data["valid"] is False

        # Step 3: Valid format
        response = api_client.post(url, {"username": "ValidName123"}, format="json")
        assert response.data["valid"] is True
        assert response.data["available"] is True

    def test_full_validation_and_update_flow(self, api_client):
        """
        Test complete flow from validation to successful update.

        User journey:
        1. Validate username → Returns valid + available
        2. Submit update → Succeeds
        3. Validate same username again → Now taken
        """
        # Create and login user
        user = User.objects.create_user(
            username="flowtest", email="flowtest@example.com", password="Pass123!"
        )
        api_client.force_authenticate(user=user)

        validate_url = reverse("authentication:username-validate")
        update_url = reverse("authentication:account-update")

        # Step 1: Validate
        response = api_client.post(validate_url, {"username": "FlowTest123"}, format="json")
        assert response.data["valid"] is True
        assert response.data["available"] is True

        # Step 2: Update
        response = api_client.patch(update_url, {"username": "FlowTest123"}, format="json")
        assert response.status_code == 200
        assert response.data["username"] == "FlowTest123"

        # Step 3: Create another user and validate same username (now taken by first user)
        other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="Pass123!"
        )
        api_client.force_authenticate(user=other_user)

        response = api_client.post(validate_url, {"username": "FlowTest123"}, format="json")
        assert response.data["valid"] is True
        assert response.data["available"] is False  # Taken by first user

    def test_validation_empty_username(self, api_client):
        """Test validation endpoint handles empty username."""
        url = reverse("authentication:username-validate")

        response = api_client.post(url, {"username": ""}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False

    def test_validation_single_char_not_allowed(self, api_client):
        """Test validation rejects single character usernames (minimum 3 chars)."""
        url = reverse("authentication:username-validate")

        response = api_client.post(url, {"username": "a"}, format="json")

        assert response.status_code == 200
        assert response.data["valid"] is False
