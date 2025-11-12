"""
Contract test: DELETE /api/account/

Test initiating account deletion.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestAccountDeleteContract:
    """Contract tests for DELETE /api/account/ endpoint."""

    def test_delete_account_returns_200(self, authenticated_client_alice):
        """
        Test that DELETE /api/account/ returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "detail": "...", "warning": "..." }
        - Sends confirmation email
        """
        url = reverse("authentication:account-delete")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "warning" in response.data
        assert "confirmation" in response.data["detail"].lower()
        assert "30 days" in response.data["warning"]

    def test_delete_account_response_schema(self, authenticated_client_alice):
        """Test response schema for account deletion request."""
        url = reverse("authentication:account-delete")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["detail"], str)
        assert isinstance(response.data["warning"], str)

    def test_delete_account_requires_authentication(self, api_client):
        """
        Test that deleting account requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-delete")
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_account_does_not_set_deleted_at_yet(
        self, authenticated_client_alice, user_alice
    ):
        """
        Test that deletion request does NOT set deleted_at immediately.

        Contract:
        - deleted_at remains NULL until email confirmation
        """
        url = reverse("authentication:account-delete")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_200_OK

        # Check deleted_at is still None
        user_alice.refresh_from_db()
        assert user_alice.deleted_at is None

    def test_delete_account_creates_account_log(self, authenticated_client_alice, user_alice):
        """
        Test that deletion request creates AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=ACCOUNT_DELETE_REQUESTED
        """
        from apps.authentication.models import AccountLog

        url = reverse("authentication:account-delete")
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_200_OK

        # Check log entry
        log = AccountLog.objects.filter(
            user=user_alice, operation="ACCOUNT_DELETE_REQUESTED"
        ).first()
        assert log is not None
