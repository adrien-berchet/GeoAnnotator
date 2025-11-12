"""
Contract test: PATCH /api/account/

Test updating account pseudonym.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAccountUpdateContract:
    """Contract tests for PATCH /api/account/ endpoint."""

    def test_update_pseudonym_returns_200(self, authenticated_client_alice):
        """
        Test that PATCH /api/account/ with valid pseudonym returns 200.

        Contract:
        - Status: 200 OK
        - Body: Updated account object
        - Request: { "pseudonym": "new_value" }
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "alice_in_wonderland"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)
        assert response.data["pseudonym"] == "alice_in_wonderland"

    def test_update_pseudonym_response_schema(self, authenticated_client_alice):
        """
        Test that updated account has correct schema.

        Contract:
        - Same schema as GET /api/account/
        - pseudonym field updated
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "alice_2024"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.data
        assert "pseudonym" in response.data
        assert "email" in response.data
        assert "created_at" in response.data
        assert "updated_at" in response.data

    def test_update_pseudonym_with_spaces_returns_400(self, authenticated_client_alice):
        """
        Test that pseudonym with spaces is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Pseudonym cannot contain spaces."
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "alice in wonderland"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pseudonym" in response.data
        assert any("space" in str(error).lower() for error in response.data["pseudonym"])

    def test_update_pseudonym_too_long_returns_400(self, authenticated_client_alice):
        """
        Test that pseudonym over 99 characters is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Max length: 99 characters
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "a" * 100}  # 100 characters
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pseudonym" in response.data

    def test_update_pseudonym_duplicate_returns_400(
        self, authenticated_client_alice, authenticated_client_bob, user_bob
    ):
        """
        Test that duplicate pseudonym is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "This pseudonym is already taken."
        - Case-insensitive uniqueness check
        """
        # Set Bob's pseudonym
        user_bob.pseudonym = "bob_the_builder"
        user_bob.save()

        # Try to use same pseudonym for Alice
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "bob_the_builder"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pseudonym" in response.data
        assert any("taken" in str(error).lower() for error in response.data["pseudonym"])

    def test_update_pseudonym_case_insensitive_duplicate_returns_400(
        self, authenticated_client_alice, authenticated_client_bob, user_bob
    ):
        """
        Test that duplicate pseudonym with different case is rejected.

        Contract:
        - Case-insensitive uniqueness: "Bob" and "bob" are duplicates
        """
        user_bob.pseudonym = "BobBuilder"
        user_bob.save()

        url = reverse("authentication:account-update")
        payload = {"pseudonym": "bobbuilder"}  # Different case
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pseudonym" in response.data

    def test_update_pseudonym_empty_returns_400(self, authenticated_client_alice):
        """
        Test that empty pseudonym is rejected.

        Contract:
        - Minimum length: 1 character
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": ""}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "pseudonym" in response.data

    def test_update_pseudonym_special_characters_allowed(self, authenticated_client_alice):
        r"""
        Test that pseudonym with allowed special characters succeeds.

        Contract:
        - Pattern: /^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+$/
        - Special characters allowed (except spaces)
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "alice_2024!@#"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["pseudonym"] == "alice_2024!@#"

    def test_update_pseudonym_requires_authentication(self, api_client):
        """
        Test that updating pseudonym requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-update")
        payload = {"pseudonym": "test"}
        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_pseudonym_creates_account_log(self, authenticated_client_alice, user_alice):
        """
        Test that updating pseudonym creates an AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=PSEUDONYM_CHANGED
        """
        from apps.authentication.models import AccountLog

        url = reverse("authentication:account-update")
        payload = {"pseudonym": "alice_new"}
        response = authenticated_client_alice.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check that log was created
        log = AccountLog.objects.filter(user=user_alice, operation="PSEUDONYM_CHANGED").first()
        assert log is not None
        assert log.details.get("new_pseudonym") == "alice_new"
