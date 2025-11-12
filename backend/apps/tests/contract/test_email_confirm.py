"""
Contract test: POST /api/account/confirm-email/

Test confirming email change with token.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status


@pytest.mark.django_db
class TestEmailConfirmContract:
    """Contract tests for POST /api/account/confirm-email/ endpoint."""

    def test_confirm_email_returns_200(self, authenticated_client_alice, user_alice):
        """
        Test that POST /api/account/confirm-email/ with valid token returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "detail": "...", "new_email": "..." }
        - Updates user email
        """
        from apps.authentication.models import EmailChangeConfirmation
        from apps.authentication.services import EmailChangeTokenGenerator

        # Create confirmation
        new_email = "alice.confirmed@example.com"
        token_generator = EmailChangeTokenGenerator()
        token = token_generator.generate_token(user_alice, new_email)

        EmailChangeConfirmation.objects.create(
            user=user_alice,
            new_email=new_email,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        url = reverse("authentication:account-confirm-email")
        payload = {"token": token, "user_id": user_alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "new_email" in response.data
        assert response.data["new_email"] == new_email

    def test_confirm_email_invalid_token_returns_400(self, authenticated_client_alice, user_alice):
        """
        Test that invalid token is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Invalid or expired confirmation token."
        """
        url = reverse("authentication:account-confirm-email")
        payload = {"token": "invalid_token_123", "user_id": user_alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "invalid" in response.data["detail"].lower()

    def test_confirm_email_expired_token_returns_400(self, authenticated_client_alice, user_alice):
        """
        Test that expired token is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Confirmation link has expired."
        """
        from apps.authentication.models import EmailChangeConfirmation
        from apps.authentication.services import EmailChangeTokenGenerator

        # Create expired confirmation
        token_generator = EmailChangeTokenGenerator()
        token = token_generator.generate_token(user_alice, "expired@example.com")

        EmailChangeConfirmation.objects.create(
            user=user_alice,
            new_email="expired@example.com",
            token=token,
            expires_at=timezone.now() - timedelta(hours=1),  # Expired
        )

        url = reverse("authentication:account-confirm-email")
        payload = {"token": token, "user_id": user_alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "detail" in response.data
        assert "expired" in response.data["detail"].lower()

    def test_confirm_email_wrong_user_returns_403(self, authenticated_client_alice, user_bob):
        """
        Test that confirming another user's email change is forbidden.

        Contract:
        - Status: 403 FORBIDDEN
        - Error: "You do not have permission to confirm this email change."
        """
        from apps.authentication.models import EmailChangeConfirmation
        from apps.authentication.services import EmailChangeTokenGenerator

        # Create confirmation for Bob
        token_generator = EmailChangeTokenGenerator()
        token = token_generator.generate_token(user_bob, "bob.new@example.com")

        EmailChangeConfirmation.objects.create(
            user=user_bob,
            new_email="bob.new@example.com",
            token=token,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        # Alice tries to confirm Bob's email change
        url = reverse("authentication:account-confirm-email")
        payload = {"token": token, "user_id": user_bob.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_confirm_email_requires_authentication(self, api_client, user_alice):
        """
        Test that confirming email requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-confirm-email")
        payload = {"token": "test_token", "user_id": user_alice.id}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_confirm_email_updates_user_email(self, authenticated_client_alice, user_alice):
        """
        Test that confirming email updates user's email field.

        Side effect:
        - Updates User.email to new email
        - Deletes EmailChangeConfirmation record
        """
        from apps.authentication.models import EmailChangeConfirmation
        from apps.authentication.services import EmailChangeTokenGenerator

        new_email = "alice.final@example.com"
        token_generator = EmailChangeTokenGenerator()
        token = token_generator.generate_token(user_alice, new_email)

        EmailChangeConfirmation.objects.create(
            user=user_alice,
            new_email=new_email,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        url = reverse("authentication:account-confirm-email")
        payload = {"token": token, "user_id": user_alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check email was updated
        user_alice.refresh_from_db()
        assert user_alice.email == new_email

        # Check confirmation was deleted
        assert not EmailChangeConfirmation.objects.filter(user=user_alice).exists()

    def test_confirm_email_creates_account_log(self, authenticated_client_alice, user_alice):
        """
        Test that confirming email creates AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=EMAIL_CHANGE_CONFIRMED
        """
        from apps.authentication.models import AccountLog
        from apps.authentication.models import EmailChangeConfirmation
        from apps.authentication.services import EmailChangeTokenGenerator

        new_email = "alice.logged@example.com"
        token_generator = EmailChangeTokenGenerator()
        token = token_generator.generate_token(user_alice, new_email)

        EmailChangeConfirmation.objects.create(
            user=user_alice,
            new_email=new_email,
            token=token,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        url = reverse("authentication:account-confirm-email")
        payload = {"token": token, "user_id": user_alice.id}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check log entry
        log = AccountLog.objects.filter(user=user_alice, operation="EMAIL_CHANGE_CONFIRMED").first()
        assert log is not None
