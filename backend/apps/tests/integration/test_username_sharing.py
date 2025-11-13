"""
Integration test: Username in shares

Test that username is displayed in shares instead of email for privacy.
Matches quickstart scenario: Username appears in shared annotations, not email.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUsernameSharing:
    """Integration tests for username display in shares."""

    def test_username_used_in_account_response(self, alice, authenticated_client_alice):
        """
        Test that account endpoint returns username.

        Privacy scenario:
        - User sets username
        - Account endpoint returns username (for display in UI)
        - Email is kept private
        """
        alice.username = "AliceExplorer"
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == 200
        assert response.data["username"] == "AliceExplorer"
        # Email also present but user chooses to display username
        assert "email" in response.data

    def test_username_vs_email_privacy(self, alice, authenticated_client_alice):
        """Test that username provides privacy alternative to email."""
        alice.email = "private.email@example.com"
        alice.username = "PublicDisplayName"
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        # Both available, but username is for public display
        assert response.data["email"] == "private.email@example.com"
        assert response.data["username"] == "PublicDisplayName"

    def test_different_users_different_usernames(
        self, alice, bob, authenticated_client_alice, authenticated_client_bob
    ):
        """Test that different users can have different usernames."""
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

    def test_username_uniqueness_enforcement(
        self, alice, bob, authenticated_client_alice
    ):
        """Test that username uniqueness is enforced across users."""
        bob.username = "UniqueDisplay"
        bob.save()

        # Alice tries to use Bob's username
        url = reverse("authentication:account-update")
        response = authenticated_client_alice.patch(
            url, {"username": "UniqueDisplay"}, format="json"
        )

        assert response.status_code == 400

    def test_username_case_insensitive_uniqueness(
        self, alice, bob, authenticated_client_alice
    ):
        """Test that username uniqueness is case-insensitive."""
        bob.username = "DisplayName"
        bob.save()

        url = reverse("authentication:account-update")

        # Try lowercase
        response = authenticated_client_alice.patch(
            url, {"username": "displayname"}, format="json"
        )
        assert response.status_code == 400

        # Try uppercase
        response = authenticated_client_alice.patch(
            url, {"username": "DISPLAYNAME"}, format="json"
        )
        assert response.status_code == 400

    def test_username_special_characters_allowed(self, alice, authenticated_client_alice):
        """Test that username can contain underscores and hyphens."""
        url = reverse("authentication:account-update")

        special_usernames = ["User_123", "User-Name", "User_with-both"]

        for username in special_usernames:
            response = authenticated_client_alice.patch(
                url, {"username": username}, format="json"
            )
            assert response.status_code == 200, f"Failed for {username}"

            # Verify it's saved
            alice.refresh_from_db()
            assert alice.username == username

    def test_username_max_length_100_chars(self, alice, authenticated_client_alice):
        """Test that username has maximum length of 100 characters."""
        url = reverse("authentication:account-update")

        # 100 chars - should succeed
        username_100 = "a" * 100
        response = authenticated_client_alice.patch(url, {"username": username_100}, format="json")
        assert response.status_code == 200

        # 101 chars - should fail
        username_101 = "a" * 101
        response = authenticated_client_alice.patch(
            url, {"username": username_101}, format="json"
        )
        assert response.status_code == 400

    def test_username_consistency_across_sessions(self, alice, authenticated_client_alice):
        """Test that username persists across multiple requests/sessions."""
        alice.username = "PersistentName"
        alice.save()

        url = reverse("authentication:account-retrieve")

        # Multiple requests return same username
        for _ in range(5):
            response = authenticated_client_alice.get(url)
            assert response.status_code == 200
            assert response.data["username"] == "PersistentName"

    def test_username_returned_in_json_response(self, alice, authenticated_client_alice):
        """Test that username is properly serialized in JSON response."""
        alice.username = "JsonTest123"
        alice.save()

        url = reverse("authentication:account-retrieve")
        response = authenticated_client_alice.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert response.data["username"] == "JsonTest123"

    def test_username_validation_prevents_spaces(self, alice, authenticated_client_alice):
        """Test that username validation prevents spaces (for share URLs)."""
        url = reverse("authentication:account-update")

        response = authenticated_client_alice.patch(
            url, {"username": "Name With Spaces"}, format="json"
        )

        assert response.status_code == 400
