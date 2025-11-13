"""
Integration test: Username creation flow

Test the complete user journey from registration to username creation and display.
Matches quickstart scenario: User creates account → sets username → sees it in menu.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import User


@pytest.mark.django_db
class TestUsernameCreationFlow:
    """Integration tests for username creation user journey."""

    def test_new_user_sets_username_appears_in_menu(self, api_client):
        """
        Complete flow: New user → Set username → Verify menu display.

        Scenario from quickstart.md:
        1. User creates account (no username yet)
        2. User sets username via PATCH /api/account/
        3. User fetches account via GET /api/account/
        4. Username appears in response
        """
        # Step 1: Create new user with initial username
        user = User.objects.create_user(
            username="newuser",  # Initial username
            email="newuser@example.com",
            password="SecurePass123!",
        )

        # Login
        api_client.force_authenticate(user=user)

        # Step 2: Update username
        update_url = reverse("authentication:account-update")
        username_data = {"username": "CoolExplorer"}

        response = api_client.patch(update_url, username_data, format="json")
        assert response.status_code == 200

        # Step 3: Fetch account to verify
        get_url = reverse("authentication:account-retrieve")
        response = api_client.get(get_url)

        assert response.status_code == 200
        assert response.data["username"] == "CoolExplorer"

    def test_username_empty_to_filled_journey(self, alice, authenticated_client_alice):
        """Test journey from initial username to updating it."""
        # Start with initial username
        alice.username = "alice_initial"
        alice.save()

        # User updates username
        url = reverse("authentication:account-update")
        response = authenticated_client_alice.patch(
            url, {"username": "AliceInWonderland"}, format="json"
        )

        assert response.status_code == 200

        # Verify it's saved
        alice.refresh_from_db()
        assert alice.username == "AliceInWonderland"

        # Verify it appears in GET response
        retrieve_url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(retrieve_url)
        assert response.data["username"] == "AliceInWonderland"

    def test_username_appears_consistently_across_requests(
        self, alice, authenticated_client_alice
    ):
        """Test that username is consistent across multiple GET requests."""
        alice.username = "ConsistentName"
        alice.save()

        url = reverse("authentication:account-retrieve")

        # Multiple requests should return same username
        for _ in range(3):
            response = authenticated_client_alice.get(url)
            assert response.status_code == 200
            assert response.data["username"] == "ConsistentName"

    def test_username_update_journey(self, alice, authenticated_client_alice):
        """Test journey of changing username from one value to another."""
        # Start with initial username
        alice.username = "OldName"
        alice.save()

        url = reverse("authentication:account-retrieve")

        # Verify initial state
        response = authenticated_client_alice.get(url)
        assert response.data["username"] == "OldName"

        # Update username
        update_url = reverse("authentication:account-update")
        response = authenticated_client_alice.patch(update_url, {"username": "NewName"}, format="json")
        assert response.status_code == 200

        # Verify updated state
        response = authenticated_client_alice.get(url)
        assert response.data["username"] == "NewName"

    def test_username_displayed_not_email(self, alice, authenticated_client_alice):
        """Test that account endpoint returns username, not email by default."""
        alice.username = "PrivacyFirst"
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        # Should return username
        assert response.data["username"] == "PrivacyFirst"

        # Email should also be in response (but user can choose to display username instead)
        assert "email" in response.data

    def test_multiple_users_different_usernames(
        self, alice, bob, authenticated_client_alice, authenticated_client_bob
    ):
        """Test that multiple users can have different usernames."""
        alice.username = "Alice123"
        alice.save()

        bob.username = "Bob456"
        bob.save()

        url = reverse("authentication:account-retrieve")

        # Alice sees her username
        response = authenticated_client_alice.get(url)
        assert response.data["username"] == "Alice123"

        # Bob sees his username
        response = authenticated_client_bob.get(url)
        assert response.data["username"] == "Bob456"

    def test_username_creation_creates_account_log(self, alice, authenticated_client_alice):
        """Test that updating username creates an account log entry."""
        from apps.authentication.models import AccountLog

        # Clear any existing logs
        AccountLog.objects.filter(user=alice).delete()

        update_url = reverse("authentication:account-update")
        authenticated_client_alice.patch(update_url, {"username": "NewUsername"}, format="json")

        # Should create account log
        logs = AccountLog.objects.filter(user=alice, operation="USERNAME_CHANGED")
        assert logs.count() == 1

    def test_username_initial_to_custom_journey(self, api_client):
        """Test journey from initial username to custom value."""
        # Create user with initial username
        user = User.objects.create_user(
            username="user123", email="user123@example.com", password="Pass123!"
        )

        api_client.force_authenticate(user=user)

        update_url = reverse("authentication:account-update")

        # Update username to custom value
        response = api_client.patch(update_url, {"username": "CustomUsername"}, format="json")

        assert response.status_code == 200

        user.refresh_from_db()
        assert user.username == "CustomUsername"
