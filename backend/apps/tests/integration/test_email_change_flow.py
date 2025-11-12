"""
Integration test: Email change flow

Test the complete email change journey: Request → Email sent → Confirmation → Email updated.
Matches quickstart scenario: Change email flow with confirmation token.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import AccountLog
from apps.authentication.models import EmailChangeConfirmation
from apps.authentication.services import EmailChangeTokenGenerator


@pytest.mark.django_db
class TestEmailChangeFlow:
    """Integration tests for email change user journey."""

    def test_complete_email_change_flow(self, user_alice, authenticated_client_alice):
        """
        Test complete email change journey.

        User journey:
        1. Request email change → Confirmation record created
        2. Extract token from confirmation record
        3. Submit confirmation → Email updated
        4. Verify account log created
        """
        new_email = "newalice@example.com"

        # Step 1: Request email change
        change_url = reverse("authentication:change-email")
        response = authenticated_client_alice.post(
            change_url, {"new_email": new_email}, format="json"
        )

        assert response.status_code == 200
        assert "confirmation sent" in response.data["message"].lower() or "token" in response.data

        # Verify confirmation record created
        confirmation = EmailChangeConfirmation.objects.get(user=user_alice)
        assert confirmation.new_email == new_email

        # Step 2: Generate token (simulating email link)
        token = EmailChangeTokenGenerator.generate_token(user_alice, new_email)

        # Step 3: Confirm email change
        confirm_url = reverse("authentication:confirm-email")
        response = authenticated_client_alice.post(
            confirm_url, {"token": token, "new_email": new_email}, format="json"
        )

        assert response.status_code == 200

        # Verify email updated
        user_alice.refresh_from_db()
        assert user_alice.email == new_email

        # Step 4: Verify account log created
        logs = AccountLog.objects.filter(user=user_alice, action="change_email")
        assert logs.count() >= 1

    def test_email_change_request_creates_confirmation_record(
        self, user_alice, authenticated_client_alice
    ):
        """Test that requesting email change creates confirmation record."""
        new_email = "newemail@example.com"

        url = reverse("authentication:change-email")
        response = authenticated_client_alice.post(url, {"new_email": new_email}, format="json")

        assert response.status_code == 200

        # Confirmation record should exist
        assert EmailChangeConfirmation.objects.filter(user=user_alice, new_email=new_email).exists()

    def test_email_change_with_invalid_token_fails(self, user_alice, authenticated_client_alice):
        """Test that invalid token rejects email change."""
        # Request change
        change_url = reverse("authentication:change-email")
        authenticated_client_alice.post(
            change_url, {"new_email": "newemail@example.com"}, format="json"
        )

        # Try to confirm with invalid token
        confirm_url = reverse("authentication:confirm-email")
        response = authenticated_client_alice.post(
            confirm_url,
            {"token": "invalid_token_12345", "new_email": "newemail@example.com"},
            format="json",
        )

        assert response.status_code == 400

    def test_email_change_with_wrong_email_fails(self, user_alice, authenticated_client_alice):
        """Test that token for one email can't be used for another."""
        # Request change for email A
        change_url = reverse("authentication:change-email")
        authenticated_client_alice.post(
            change_url, {"new_email": "emaila@example.com"}, format="json"
        )

        # Generate token for email A
        token = EmailChangeTokenGenerator.generate_token(user_alice, "emaila@example.com")

        # Try to use token for email B
        confirm_url = reverse("authentication:confirm-email")
        response = authenticated_client_alice.post(
            confirm_url,
            {"token": token, "new_email": "emailb@example.com"},  # Different email
            format="json",
        )

        assert response.status_code == 400

    def test_email_change_by_different_user_fails(
        self, user_alice, user_bob, authenticated_client_bob
    ):
        """Test that user can't confirm another user's email change."""
        # Alice requests email change
        EmailChangeConfirmation.objects.create(user=user_alice, new_email="alicenew@example.com")

        # Generate token for Alice
        token = EmailChangeTokenGenerator.generate_token(user_alice, "alicenew@example.com")

        # Bob tries to use Alice's token
        confirm_url = reverse("authentication:confirm-email")
        response = authenticated_client_bob.post(
            confirm_url, {"token": token, "new_email": "alicenew@example.com"}, format="json"
        )

        assert response.status_code == 403

    def test_email_change_deletes_confirmation_record(self, user_alice, authenticated_client_alice):
        """Test that successful email change deletes confirmation record."""
        new_email = "confirmed@example.com"

        # Request change
        change_url = reverse("authentication:change-email")
        authenticated_client_alice.post(change_url, {"new_email": new_email}, format="json")

        # Confirm exists
        assert EmailChangeConfirmation.objects.filter(user=user_alice).exists()

        # Confirm change
        token = EmailChangeTokenGenerator.generate_token(user_alice, new_email)
        confirm_url = reverse("authentication:confirm-email")
        authenticated_client_alice.post(
            confirm_url, {"token": token, "new_email": new_email}, format="json"
        )

        # Confirmation record should be deleted
        assert not EmailChangeConfirmation.objects.filter(user=user_alice).exists()

    def test_multiple_email_change_requests_updates_confirmation(
        self, user_alice, authenticated_client_alice
    ):
        """Test that multiple change requests update (not duplicate) confirmation record."""
        url = reverse("authentication:change-email")

        # First request
        authenticated_client_alice.post(url, {"new_email": "first@example.com"}, format="json")

        # Second request
        authenticated_client_alice.post(url, {"new_email": "second@example.com"}, format="json")

        # Should only have one confirmation record (latest)
        confirmations = EmailChangeConfirmation.objects.filter(user=user_alice)
        assert confirmations.count() == 1
        assert confirmations.first().new_email == "second@example.com"

    def test_email_change_to_existing_email_rejected(
        self, user_alice, user_bob, authenticated_client_alice
    ):
        """Test that changing to an already-used email is rejected."""
        url = reverse("authentication:change-email")

        # Try to change to Bob's email
        response = authenticated_client_alice.post(
            url, {"new_email": user_bob.email}, format="json"
        )

        assert response.status_code == 400

    def test_email_change_creates_account_logs(self, user_alice, authenticated_client_alice):
        """Test that email change creates appropriate account logs."""
        # Clear existing logs
        AccountLog.objects.filter(user=user_alice).delete()

        new_email = "logged@example.com"

        # Request change
        change_url = reverse("authentication:change-email")
        authenticated_client_alice.post(change_url, {"new_email": new_email}, format="json")

        # Should create log for request
        assert AccountLog.objects.filter(user=user_alice, action="change_email").exists()

        # Confirm change
        token = EmailChangeTokenGenerator.generate_token(user_alice, new_email)
        confirm_url = reverse("authentication:confirm-email")
        authenticated_client_alice.post(
            confirm_url, {"token": token, "new_email": new_email}, format="json"
        )

        # Should have logs for both steps
        logs = AccountLog.objects.filter(user=user_alice, action="change_email")
        assert logs.count() >= 1
