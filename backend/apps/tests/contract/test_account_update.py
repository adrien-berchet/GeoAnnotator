"""
Contract test: PATCH /api/account/

Test updating account username.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAccountUpdateContract:
    """Contract tests for PATCH /api/account/ endpoint."""

    def test_update_username_returns_200(self, authenticated_client_alice):
        """
        Test that PATCH /api/account/ with valid username returns 200.

        Contract:
        - Status: 200 OK
        - Body: Updated account object
        - Request: { "username": "new_value" }
        """
        url = reverse("authentication:account-update")
        payload = {"username": "alice_in_wonderland"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert response.data["username"] == "alice_in_wonderland"

    def test_update_username_response_schema(self, authenticated_client_alice):
        """
        Test that updated account has correct schema.

        Contract:
        - Same schema as GET /api/account/
        - username field updated
        """
        url = reverse("authentication:account-update")
        payload = {"username": "alice_2024"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.data
        assert "username" in response.data
        assert "email" in response.data
        assert "date_joined" in response.data

    def test_update_username_with_spaces_returns_400(self, authenticated_client_alice):
        """
        Test that username with spaces is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Username cannot contain spaces."
        """
        url = reverse("authentication:account-update")
        payload = {"username": "alice in wonderland"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "username" in response.data["details"]
        assert any("space" in str(error).lower() for error in response.data["details"]["username"])

    def test_update_username_too_long_returns_400(self, authenticated_client_alice):
        """
        Test that username over 100 characters is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Max length: 100 characters
        """
        url = reverse("authentication:account-update")
        payload = {"username": "a" * 101}  # 101 characters
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "username" in response.data["details"]

    def test_update_username_duplicate_returns_400(
        self, authenticated_client_alice, authenticated_client_bob, bob
    ):
        """
        Test that duplicate username is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "This username is already taken."
        - Case-insensitive uniqueness check
        """
        # Set Bob's username
        bob.username = "bob_the_builder"
        bob.save()

        # Try to use same username for Alice
        url = reverse("authentication:account-update")
        payload = {"username": "bob_the_builder"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "username" in response.data["details"]
        assert any("taken" in str(error).lower() for error in response.data["details"]["username"])

    def test_update_username_case_insensitive_duplicate_returns_400(
        self, authenticated_client_alice, authenticated_client_bob, bob
    ):
        """
        Test that duplicate username with different case is rejected.

        Contract:
        - Case-insensitive uniqueness: "Bob" and "bob" are duplicates
        """
        bob.username = "BobBuilder"
        bob.save()

        url = reverse("authentication:account-update")
        payload = {"username": "bobbuilder"}  # Different case
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "username" in response.data["details"]

    def test_update_username_empty_returns_400(self, authenticated_client_alice):
        """
        Test that empty username is rejected.

        Contract:
        - Minimum length: 1 character
        """
        url = reverse("authentication:account-update")
        payload = {"username": ""}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "username" in response.data["details"]

    def test_update_username_special_characters_allowed(self, authenticated_client_alice):
        r"""
        Test that username with allowed special characters succeeds.

        Contract:
        - Pattern: /^[a-zA-Z0-9][a-zA-Z0-9_\-]*$/
        - Only underscore and hyphen allowed as special characters
        """
        url = reverse("authentication:account-update")
        payload = {"username": "alice_2024-test"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "alice_2024-test"

    def test_update_username_requires_authentication(self, api_client):
        """
        Test that updating username requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-update")
        payload = {"username": "test"}
        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_username_creates_account_log(self, authenticated_client_alice, alice):
        """
        Test that updating username creates an AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=USERNAME_CHANGED
        """
        from apps.authentication.models import AccountLog

        url = reverse("authentication:account-update")
        payload = {"username": "alice_new"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check that log was created
        log = AccountLog.objects.filter(user=alice, operation="USERNAME_CHANGED").first()
        assert log is not None
        assert log.details.get("new_username") == "alice_new"
