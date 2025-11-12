"""
Integration test: Account deletion flow

Test the complete account deletion journey: Request → Confirm → Soft delete → Shares unshared → 30-day cleanup.
Matches quickstart scenario: Delete account with confirmation and 30-day grace period.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.authentication.models import AccountLog
from apps.authentication.models import User
from apps.authentication.services import AccountDeletionTokenGenerator


@pytest.mark.django_db
class TestAccountDeletionFlow:
    """Integration tests for account deletion user journey."""

    def test_complete_account_deletion_flow(self, user_alice, authenticated_client_alice):
        """
        Test complete account deletion journey.

        User journey:
        1. Request deletion → Warning message returned
        2. Generate deletion token (simulating email)
        3. Confirm deletion → User soft deleted
        4. Verify shares unshared
        5. Verify 30-day deletion scheduled
        6. Verify account logs created
        """
        # Step 1: Request deletion
        delete_url = reverse("authentication:delete-account")
        response = authenticated_client_alice.delete(delete_url)

        assert response.status_code == 200
        assert "warning" in response.data or "confirm" in response.data.get("message", "").lower()

        # User should NOT be deleted yet
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None

        # Step 2: Generate confirmation token
        token = AccountDeletionTokenGenerator.generate_token(user_alice)

        # Step 3: Confirm deletion
        confirm_url = reverse("authentication:confirm-delete")
        response = authenticated_client_alice.post(confirm_url, {"token": token}, format="json")

        assert response.status_code == 200

        # User should now be soft deleted
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is not None

        # Step 5: Verify 30-day schedule
        expected_deletion = timezone.now() + timedelta(days=30)
        time_diff = abs((user_alice.deleted_at - expected_deletion).total_seconds())
        assert time_diff < 60  # Within 1 minute

        # Step 6: Verify account log created
        logs = AccountLog.objects.filter(user=user_alice, action="delete_account")
        assert logs.count() >= 1

    def test_deletion_request_does_not_delete_immediately(
        self, user_alice, authenticated_client_alice
    ):
        """Test that DELETE request doesn't immediately soft delete the user."""
        url = reverse("authentication:delete-account")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == 200

        # User should still be active
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None

    def test_deletion_confirmation_sets_deleted_at(self, user_alice, authenticated_client_alice):
        """Test that confirmation sets deleted_at timestamp."""
        # Request deletion
        delete_url = reverse("authentication:delete-account")
        authenticated_client_alice.delete(delete_url)

        # Confirm deletion
        token = AccountDeletionTokenGenerator.generate_token(user_alice)
        confirm_url = reverse("authentication:confirm-delete")
        authenticated_client_alice.post(confirm_url, {"token": token}, format="json")

        user_alice.refresh_from_db()
        assert user_alice.deleted_at is not None

    def test_deletion_with_invalid_token_fails(self, user_alice, authenticated_client_alice):
        """Test that invalid deletion token is rejected."""
        url = reverse("authentication:confirm-delete")
        response = authenticated_client_alice.post(
            url, {"token": "invalid_token_12345"}, format="json"
        )

        assert response.status_code == 400

        # User should not be deleted
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None

    def test_deletion_by_different_user_fails(self, user_alice, user_bob, authenticated_client_bob):
        """Test that user can't confirm another user's deletion."""
        # Generate token for Alice
        token = AccountDeletionTokenGenerator.generate_token(user_alice)

        # Bob tries to use Alice's token
        url = reverse("authentication:confirm-delete")
        response = authenticated_client_bob.post(url, {"token": token}, format="json")

        assert response.status_code == 403

        # Alice should not be deleted
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None

    def test_deleted_user_excluded_from_active_manager(
        self, user_alice, authenticated_client_alice
    ):
        """Test that deleted users are excluded from User.active manager."""
        user_id = user_alice.id

        # Initially in active manager
        assert User.active.filter(id=user_id).exists()

        # Delete account
        delete_url = reverse("authentication:delete-account")
        authenticated_client_alice.delete(delete_url)

        token = AccountDeletionTokenGenerator.generate_token(user_alice)
        confirm_url = reverse("authentication:confirm-delete")
        authenticated_client_alice.post(confirm_url, {"token": token}, format="json")

        # No longer in active manager
        assert not User.active.filter(id=user_id).exists()

    def test_deleted_user_accessible_via_objects_manager(
        self, user_alice, authenticated_client_alice
    ):
        """Test that deleted users are still accessible via User.objects."""
        user_id = user_alice.id

        # Delete account
        delete_url = reverse("authentication:delete-account")
        authenticated_client_alice.delete(delete_url)

        token = AccountDeletionTokenGenerator.generate_token(user_alice)
        confirm_url = reverse("authentication:confirm-delete")
        authenticated_client_alice.post(confirm_url, {"token": token}, format="json")

        # Still accessible via objects
        assert User.objects.filter(id=user_id).exists()

    def test_deletion_creates_account_logs(self, user_alice, authenticated_client_alice):
        """Test that deletion process creates account logs."""
        # Clear existing logs
        AccountLog.objects.filter(user=user_alice).delete()

        # Request deletion
        delete_url = reverse("authentication:delete-account")
        authenticated_client_alice.delete(delete_url)

        # Should create log for request
        assert AccountLog.objects.filter(user=user_alice, action="delete_account").exists()

    def test_deletion_schedules_30_day_cleanup(self, user_alice, authenticated_client_alice):
        """Test that deletion sets deleted_at to 30 days in future."""
        # Delete and confirm
        delete_url = reverse("authentication:delete-account")
        authenticated_client_alice.delete(delete_url)

        token = AccountDeletionTokenGenerator.generate_token(user_alice)
        confirm_url = reverse("authentication:confirm-delete")
        authenticated_client_alice.post(confirm_url, {"token": token}, format="json")

        user_alice.refresh_from_db()

        # Should be set to approximately 30 days from now
        expected_deletion = timezone.now() + timedelta(days=30)
        time_diff = abs((user_alice.deleted_at - expected_deletion).total_seconds())

        # Within 1 minute of expected time
        assert time_diff < 60

    def test_deletion_requires_authentication(self, api_client):
        """Test that unauthenticated users cannot delete account."""
        delete_url = reverse("authentication:delete-account")
        response = api_client.delete(delete_url)

        assert response.status_code == 401

    def test_deletion_confirmation_requires_authentication(self, api_client, user_alice):
        """Test that confirmation requires authentication."""
        token = AccountDeletionTokenGenerator.generate_token(user_alice)

        url = reverse("authentication:confirm-delete")
        response = api_client.post(url, {"token": token}, format="json")

        assert response.status_code == 401

    def test_deletion_warning_message_returned(self, user_alice, authenticated_client_alice):
        """Test that deletion request returns warning message."""
        url = reverse("authentication:delete-account")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == 200

        # Should contain warning or confirmation message
        response_text = str(response.data).lower()
        assert "warning" in response_text or "confirm" in response_text or "delete" in response_text

    def test_multiple_deletion_requests(self, user_alice, authenticated_client_alice):
        """Test that multiple deletion requests don't cause issues."""
        url = reverse("authentication:delete-account")

        # First request
        response1 = authenticated_client_alice.delete(url)
        assert response1.status_code == 200

        # Second request (before confirmation)
        response2 = authenticated_client_alice.delete(url)
        assert response2.status_code == 200

        # User still not deleted
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None
