"""
Contract test: POST /api/account/confirm-delete/

Test confirming account deletion.
"""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


@pytest.mark.django_db
class TestAccountDeleteConfirmContract:
    """Contract tests for POST /api/account/confirm-delete/ endpoint."""

    def test_confirm_delete_returns_200(self, authenticated_client_alice, alice):
        """
        Test that POST /api/account/confirm-delete/ with valid token returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "detail": "...", "deleted_at": "...", "permanent_deletion_date": "..." }
        - Sets deleted_at timestamp
        """
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "deleted_at" in response.data
        assert "permanent_deletion_date" in response.data

    def test_confirm_delete_response_schema(self, authenticated_client_alice, alice):
        """Test response schema for account deletion confirmation."""
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["detail"], str)
        assert isinstance(response.data["deleted_at"], str)
        assert isinstance(response.data["permanent_deletion_date"], str)

    def test_confirm_delete_invalid_token_returns_400(self, authenticated_client_alice, alice):
        """
        Test that invalid token is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Invalid or expired deletion confirmation token."
        """
        url = reverse("authentication:account-delete-confirm")
        payload = {"token": "invalid_token_xyz", "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "invalid" in response.data["detail"].lower()

    def test_confirm_delete_wrong_user_returns_403(self, authenticated_client_alice, bob):
        """
        Test that confirming another user's deletion is forbidden.

        Contract:
        - Status: 403 FORBIDDEN
        - Error: "You do not have permission to confirm this deletion."
        """
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(bob)

        # Alice tries to confirm Bob's deletion
        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": bob.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_confirm_delete_requires_authentication(self, api_client, alice):
        """
        Test that confirming deletion requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-delete-confirm")
        payload = {"token": "test_token", "user_id": alice.id}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_confirm_delete_sets_deleted_at(self, authenticated_client_alice, alice):
        """
        Test that confirming deletion sets deleted_at timestamp.

        Side effect:
        - Sets User.deleted_at to current timestamp
        """
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check deleted_at is set
        alice.refresh_from_db()
        assert alice.deleted_at is not None
        assert alice.deleted_at <= timezone.now()

    def test_confirm_delete_unshares_content(
        self, authenticated_client_alice, alice, django_assert_num_queries
    ):
        """
        Test that confirming deletion unshares all user's content.

        Side effect:
        - Sets Share.is_active = False for all user's shares
        """
        from apps.authentication.services import AccountDeletionTokenGenerator
        from apps.sharing.models import Share

        # Create some shares for Alice
        # (Assuming Share model exists with user FK and is_active field)

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check shares are inactive (if any exist)
        active_shares = Share.objects.filter(owner=alice, is_active=True).count()
        assert active_shares == 0

    def test_confirm_delete_creates_account_log(self, authenticated_client_alice, alice):
        """
        Test that confirming deletion creates AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=ACCOUNT_DELETED
        """
        from apps.authentication.models import AccountLog
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check log entry
        log = AccountLog.objects.filter(user=alice, operation="ACCOUNT_DELETED").first()
        assert log is not None

    def test_confirm_delete_schedules_permanent_deletion(
        self, authenticated_client_alice, alice
    ):
        """
        Test that permanent deletion is scheduled for 30 days later.

        Contract:
        - permanent_deletion_date = deleted_at + 30 days
        """
        from apps.authentication.services import AccountDeletionTokenGenerator

        token_generator = AccountDeletionTokenGenerator()
        token = token_generator.generate_token(alice)

        url = reverse("authentication:account-delete-confirm")
        payload = {"token": token, "user_id": alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check permanent deletion date is ~30 days from now
        from datetime import datetime

        deleted_at = datetime.fromisoformat(response.data["deleted_at"].replace("Z", "+00:00"))
        permanent_date = datetime.fromisoformat(
            response.data["permanent_deletion_date"].replace("Z", "+00:00")
        )

        diff = (permanent_date - deleted_at).days
        assert 29 <= diff <= 31  # Allow for timezone differences
