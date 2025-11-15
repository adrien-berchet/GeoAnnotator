"""
Contract test: POST /api/account/change-email/

Test initiating email change process.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestEmailChangeContract:
    """Contract tests for POST /api/account/change-email/ endpoint."""

    def test_change_email_returns_200(self, authenticated_client_alice):
        """
        Test that POST /api/account/change-email/ returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "detail": "...", "expires_at": "..." }
        - Sends confirmation email
        """
        url = reverse("authentication:email-change")
        payload = {"new_email": "alice.new@example.com"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "expires_at" in response.data
        assert "confirmation email sent" in response.data["detail"].lower()

    def test_change_email_response_schema(self, authenticated_client_alice):
        """Test response schema for email change request."""
        url = reverse("authentication:email-change")
        payload = {"new_email": "alice.updated@example.com"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["detail"], str)
        assert isinstance(response.data["expires_at"], str)

    def test_change_email_invalid_email_returns_400(self, authenticated_client_alice):
        """
        Test that invalid email format is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Enter a valid email address."
        """
        url = reverse("authentication:email-change")
        payload = {"new_email": "not-an-email"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_email" in response.data.get("details", {})

    def test_change_email_duplicate_returns_400(self, authenticated_client_alice, bob):
        """
        Test that email already in use is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "This email address is already in use."
        """
        url = reverse("authentication:email-change")
        payload = {"new_email": bob.email}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "new_email" in response.data["details"]
        assert any(
            "already in use" in str(error).lower()
            for error in response.data["details"]["new_email"]
        )

    def test_change_email_same_as_current_returns_400(self, authenticated_client_alice, alice):
        """
        Test that same email as current is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "New email must be different from current email."
        """
        url = reverse("authentication:email-change")
        payload = {"new_email": alice.email}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "details" in response.data
        assert "new_email" in response.data["details"]

    def test_change_email_requires_authentication(self, api_client):
        """
        Test that changing email requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:email-change")
        payload = {"new_email": "test@example.com"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_email_creates_confirmation_record(self, authenticated_client_alice, alice):
        """
        Test that email change creates EmailChangeConfirmation record.

        Side effect:
        - Creates EmailChangeConfirmation with token
        - Token expires in 30 minutes
        """
        from apps.authentication.models import EmailConfirmation

        url = reverse("authentication:email-change")
        payload = {"new_email": "alice.confirmed@example.com"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check confirmation record
        confirmation = EmailConfirmation.objects.filter(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        ).first()
        assert confirmation is not None
        assert confirmation.new_email == "alice.confirmed@example.com"
        assert confirmation.token is not None
        assert confirmation.expires_at is not None

    def test_change_email_creates_account_log(self, authenticated_client_alice, alice):
        """
        Test that email change request creates AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=EMAIL_CHANGE_REQUESTED
        """
        from apps.authentication.models import AccountLog

        url = reverse("authentication:email-change")
        payload = {"new_email": "alice.logged@example.com"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check log entry
        log = AccountLog.objects.filter(user=alice, operation="EMAIL_CHANGE_REQUESTED").first()
        assert log is not None
