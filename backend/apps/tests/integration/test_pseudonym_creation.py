"""
Integration test: Pseudonym creation flow

Test the complete user journey from registration to pseudonym creation and display.
Matches quickstart scenario: User creates account → sets pseudonym → sees it in menu.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import User


@pytest.mark.django_db
class TestPseudonymCreationFlow:
    """Integration tests for pseudonym creation user journey."""

    def test_new_user_sets_pseudonym_appears_in_menu(self, api_client):
        """
        Complete flow: New user → Set pseudonym → Verify menu display.

        Scenario from quickstart.md:
        1. User creates account (no pseudonym yet)
        2. User sets pseudonym via PATCH /api/account/
        3. User fetches account via GET /api/account/
        4. Pseudonym appears in response
        """
        # Step 1: Create new user
        user = User.objects.create_user(
            email="newuser@example.com",
            password="SecurePass123!",
            pseudonym="",  # No pseudonym initially
        )

        # Login
        api_client.force_authenticate(user=user)

        # Step 2: Set pseudonym
        update_url = reverse("authentication:account-detail")
        pseudonym_data = {"pseudonym": "CoolExplorer"}

        response = api_client.patch(update_url, pseudonym_data, format="json")
        assert response.status_code == 200

        # Step 3: Fetch account to verify
        get_url = reverse("authentication:account-detail")
        response = api_client.get(get_url)

        assert response.status_code == 200
        assert response.data["pseudonym"] == "CoolExplorer"

    def test_pseudonym_empty_to_filled_journey(self, user_alice, authenticated_client_alice):
        """Test journey from no pseudonym to setting one."""
        # Start with empty pseudonym
        user_alice.pseudonym = ""
        user_alice.save()

        # User sets pseudonym
        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.patch(
            url, {"pseudonym": "AliceInWonderland"}, format="json"
        )

        assert response.status_code == 200

        # Verify it's saved
        user_alice.refresh_from_db()
        assert user_alice.pseudonym == "AliceInWonderland"

        # Verify it appears in GET response
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == "AliceInWonderland"

    def test_pseudonym_appears_consistently_across_requests(
        self, user_alice, authenticated_client_alice
    ):
        """Test that pseudonym is consistent across multiple GET requests."""
        user_alice.pseudonym = "ConsistentName"
        user_alice.save()

        url = reverse("authentication:account-detail")

        # Multiple requests should return same pseudonym
        for _ in range(3):
            response = authenticated_client_alice.get(url)
            assert response.status_code == 200
            assert response.data["pseudonym"] == "ConsistentName"

    def test_pseudonym_update_journey(self, user_alice, authenticated_client_alice):
        """Test journey of changing pseudonym from one value to another."""
        # Start with initial pseudonym
        user_alice.pseudonym = "OldName"
        user_alice.save()

        url = reverse("authentication:account-detail")

        # Verify initial state
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == "OldName"

        # Update pseudonym
        response = authenticated_client_alice.patch(url, {"pseudonym": "NewName"}, format="json")
        assert response.status_code == 200

        # Verify updated state
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == "NewName"

    def test_pseudonym_displayed_not_email(self, user_alice, authenticated_client_alice):
        """Test that account endpoint returns pseudonym, not email by default."""
        user_alice.pseudonym = "PrivacyFirst"
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        # Should return pseudonym
        assert response.data["pseudonym"] == "PrivacyFirst"

        # Email should also be in response (but user can choose to display pseudonym instead)
        assert "email" in response.data

    def test_multiple_users_different_pseudonyms(
        self, user_alice, user_bob, authenticated_client_alice, authenticated_client_bob
    ):
        """Test that multiple users can have different pseudonyms."""
        user_alice.pseudonym = "Alice123"
        user_alice.save()

        user_bob.pseudonym = "Bob456"
        user_bob.save()

        url = reverse("authentication:account-detail")

        # Alice sees her pseudonym
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == "Alice123"

        # Bob sees his pseudonym
        response = authenticated_client_bob.get(url)
        assert response.data["pseudonym"] == "Bob456"

    def test_pseudonym_creation_creates_account_log(self, user_alice, authenticated_client_alice):
        """Test that setting pseudonym creates an account log entry."""
        from apps.authentication.models import AccountLog

        user_alice.pseudonym = ""
        user_alice.save()

        # Clear any existing logs
        AccountLog.objects.filter(user=user_alice).delete()

        url = reverse("authentication:account-detail")
        authenticated_client_alice.patch(url, {"pseudonym": "NewPseudonym"}, format="json")

        # Should create account log
        logs = AccountLog.objects.filter(user=user_alice, action="update_pseudonym")
        assert logs.count() == 1

    def test_pseudonym_null_to_value_journey(self, api_client):
        """Test journey from NULL pseudonym to a value."""
        # Create user with NULL pseudonym
        user = User.objects.create_user(
            email="nullpseudo@example.com", password="Pass123!", pseudonym=None
        )

        api_client.force_authenticate(user=user)

        url = reverse("authentication:account-detail")

        # Set pseudonym
        response = api_client.patch(url, {"pseudonym": "FirstPseudonym"}, format="json")

        assert response.status_code == 200

        user.refresh_from_db()
        assert user.pseudonym == "FirstPseudonym"
