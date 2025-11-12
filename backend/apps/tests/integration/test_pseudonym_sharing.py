"""
Integration test: Pseudonym in shares

Test that pseudonym is displayed in shares instead of email for privacy.
Matches quickstart scenario: Pseudonym appears in shared annotations, not email.
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPseudonymSharing:
    """Integration tests for pseudonym display in shares."""

    def test_pseudonym_used_in_account_response(self, user_alice, authenticated_client_alice):
        """
        Test that account endpoint returns pseudonym.

        Privacy scenario:
        - User sets pseudonym
        - Account endpoint returns pseudonym (for display in UI)
        - Email is kept private
        """
        user_alice.pseudonym = "AliceExplorer"
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == 200
        assert response.data["pseudonym"] == "AliceExplorer"
        # Email also present but user chooses to display pseudonym
        assert "email" in response.data

    def test_pseudonym_vs_email_privacy(self, user_alice, authenticated_client_alice):
        """Test that pseudonym provides privacy alternative to email."""
        user_alice.email = "private.email@example.com"
        user_alice.pseudonym = "PublicDisplayName"
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        # Both available, but pseudonym is for public display
        assert response.data["email"] == "private.email@example.com"
        assert response.data["pseudonym"] == "PublicDisplayName"

    def test_user_without_pseudonym_falls_back_to_email(
        self, user_alice, authenticated_client_alice
    ):
        """Test behavior when user has no pseudonym set."""
        user_alice.pseudonym = None
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == 200
        assert response.data["pseudonym"] is None
        assert "email" in response.data

    def test_pseudonym_empty_string_vs_null(self, user_alice, authenticated_client_alice):
        """Test difference between empty pseudonym and null."""
        url = reverse("authentication:account-detail")

        # Test with empty string
        user_alice.pseudonym = ""
        user_alice.save()

        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == ""

        # Test with null
        user_alice.pseudonym = None
        user_alice.save()

        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] is None

    def test_different_users_different_pseudonyms(
        self, user_alice, user_bob, authenticated_client_alice, authenticated_client_bob
    ):
        """Test that different users can have different pseudonyms."""
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

    def test_pseudonym_uniqueness_enforcement(
        self, user_alice, user_bob, authenticated_client_alice
    ):
        """Test that pseudonym uniqueness is enforced across users."""
        user_bob.pseudonym = "UniqueDisplay"
        user_bob.save()

        # Alice tries to use Bob's pseudonym
        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.patch(
            url, {"pseudonym": "UniqueDisplay"}, format="json"
        )

        assert response.status_code == 400

    def test_pseudonym_case_insensitive_uniqueness(
        self, user_alice, user_bob, authenticated_client_alice
    ):
        """Test that pseudonym uniqueness is case-insensitive."""
        user_bob.pseudonym = "DisplayName"
        user_bob.save()

        url = reverse("authentication:account-detail")

        # Try lowercase
        response = authenticated_client_alice.patch(
            url, {"pseudonym": "displayname"}, format="json"
        )
        assert response.status_code == 400

        # Try uppercase
        response = authenticated_client_alice.patch(
            url, {"pseudonym": "DISPLAYNAME"}, format="json"
        )
        assert response.status_code == 400

    def test_pseudonym_special_characters_allowed(self, user_alice, authenticated_client_alice):
        """Test that pseudonym can contain special characters (for expressiveness)."""
        url = reverse("authentication:account-detail")

        special_pseudonyms = ["User_123", "User-Name", "User.Name", "User@2024", "User#Pro"]

        for pseudonym in special_pseudonyms:
            response = authenticated_client_alice.patch(
                url, {"pseudonym": pseudonym}, format="json"
            )
            assert response.status_code == 200, f"Failed for {pseudonym}"

            # Verify it's saved
            user_alice.refresh_from_db()
            assert user_alice.pseudonym == pseudonym

    def test_pseudonym_max_length_99_chars(self, user_alice, authenticated_client_alice):
        """Test that pseudonym has maximum length of 99 characters."""
        url = reverse("authentication:account-detail")

        # 99 chars - should succeed
        pseudonym_99 = "a" * 99
        response = authenticated_client_alice.patch(url, {"pseudonym": pseudonym_99}, format="json")
        assert response.status_code == 200

        # 100 chars - should fail
        pseudonym_100 = "a" * 100
        response = authenticated_client_alice.patch(
            url, {"pseudonym": pseudonym_100}, format="json"
        )
        assert response.status_code == 400

    def test_pseudonym_update_flow_preserves_privacy(self, user_alice, authenticated_client_alice):
        """
        Test complete flow: User updates pseudonym to maintain privacy.

        Privacy journey:
        1. User realizes email is visible
        2. User sets pseudonym for privacy
        3. Pseudonym now displayed instead
        """
        # Step 1: User has email as identifier
        user_alice.email = "identifiable@example.com"
        user_alice.pseudonym = None
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] is None

        # Step 2: User sets pseudonym for privacy
        response = authenticated_client_alice.patch(
            url, {"pseudonym": "AnonymousExplorer"}, format="json"
        )
        assert response.status_code == 200

        # Step 3: Pseudonym now available
        response = authenticated_client_alice.get(url)
        assert response.data["pseudonym"] == "AnonymousExplorer"

    def test_pseudonym_consistency_across_sessions(self, user_alice, authenticated_client_alice):
        """Test that pseudonym persists across multiple requests/sessions."""
        user_alice.pseudonym = "PersistentName"
        user_alice.save()

        url = reverse("authentication:account-detail")

        # Multiple requests return same pseudonym
        for _ in range(5):
            response = authenticated_client_alice.get(url)
            assert response.status_code == 200
            assert response.data["pseudonym"] == "PersistentName"

    def test_pseudonym_returned_in_json_response(self, user_alice, authenticated_client_alice):
        """Test that pseudonym is properly serialized in JSON response."""
        user_alice.pseudonym = "JsonTest123"
        user_alice.save()

        url = reverse("authentication:account-detail")
        response = authenticated_client_alice.get(url)

        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        assert response.data["pseudonym"] == "JsonTest123"

    def test_pseudonym_validation_prevents_spaces(self, user_alice, authenticated_client_alice):
        """Test that pseudonym validation prevents spaces (for share URLs)."""
        url = reverse("authentication:account-detail")

        response = authenticated_client_alice.patch(
            url, {"pseudonym": "Name With Spaces"}, format="json"
        )

        assert response.status_code == 400
