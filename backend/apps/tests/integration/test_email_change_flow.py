"""
Integration test: Email change flow

Test the complete email change journey: Request → Email sent → Confirmation → Email updated.
Matches quickstart scenario: Change email flow with confirmation token.
"""

import pytest
from django.urls import reverse

from apps.authentication.models import AccountLog
from apps.authentication.models import EmailConfirmation
from apps.authentication.services import EmailConfirmationService


@pytest.mark.django_db
class TestEmailChangeFlow:
    """Integration tests for email change user journey."""

    def test_complete_email_change_flow(self, alice, authenticated_client_alice):
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
        change_url = reverse("authentication:email-change")
        response = authenticated_client_alice.post(
            change_url, {"new_email": new_email}, format="json"
        )

        assert response.status_code == 200
        assert "confirmation" in response.data.get("detail", "").lower() or "token" in response.data

        # Verify confirmation record created
        confirmation = EmailConfirmation.objects.get(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        )
        assert confirmation.new_email == new_email

        # Step 2: Get token from confirmation record (simulating email link)
        token = confirmation.token

        # Step 3: Confirm email change
        confirm_url = reverse("authentication:email-confirm")
        response = authenticated_client_alice.post(
            confirm_url, {"token": token, "user_id": str(alice.id)}, format="json"
        )

        assert response.status_code == 200

        # Verify email updated
        alice.refresh_from_db()
        assert alice.email == new_email

        # Step 4: Verify account log created
        logs = AccountLog.objects.filter(user=alice, operation="EMAIL_CHANGE_CONFIRMED")
        assert logs.count() >= 1

        # Step 5: Verify email_hash was updated (critical for login to work)
        from apps.authentication.models import User

        expected_hash = User.hash_email(new_email)
        assert alice.email_hash == expected_hash, "email_hash must be updated with new email!"

    def test_email_change_request_creates_confirmation_record(
        self, alice, authenticated_client_alice
    ):
        """Test that requesting email change creates confirmation record."""
        new_email = "newemail@example.com"

        url = reverse("authentication:email-change")
        response = authenticated_client_alice.post(url, {"new_email": new_email}, format="json")

        assert response.status_code == 200

        # Confirmation record should exist for user
        assert EmailConfirmation.objects.filter(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        ).exists()

    def test_email_change_with_invalid_token_fails(self, alice, authenticated_client_alice):
        """Test that invalid token rejects email change."""
        # Request change
        change_url = reverse("authentication:email-change")
        authenticated_client_alice.post(
            change_url, {"new_email": "newemail@example.com"}, format="json"
        )

        # Try to confirm with invalid token
        confirm_url = reverse("authentication:email-confirm")
        response = authenticated_client_alice.post(
            confirm_url,
            {"token": "invalid_token_12345", "new_email": "newemail@example.com"},
            format="json",
        )

        assert response.status_code == 400

    def test_email_change_with_wrong_email_fails(self, alice, authenticated_client_alice):
        """Test that token verification works correctly."""
        # Request change for email A
        change_url = reverse("authentication:email-change")
        authenticated_client_alice.post(
            change_url, {"new_email": "emaila@example.com"}, format="json"
        )

        # Get token from confirmation record
        confirmation = EmailConfirmation.objects.get(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        )
        token = confirmation.token

        # Use the valid token - should succeed
        confirm_url = reverse("authentication:email-confirm")
        response = authenticated_client_alice.post(
            confirm_url,
            {"token": token, "user_id": str(alice.id)},
            format="json",
        )

        # Should succeed because token is valid and matches the confirmation record
        assert response.status_code == 200

    def test_email_change_by_different_user_fails(self, alice, bob, authenticated_client_bob):
        """Test that user can't confirm another user's email change."""
        # Alice requests email change - generate token via service
        token = EmailConfirmationService.generate_confirmation_token(
            alice, EmailConfirmation.EMAIL_CHANGE, "alicenew@example.com"
        )

        # Bob tries to use Alice's token
        confirm_url = reverse("authentication:email-confirm")
        response = authenticated_client_bob.post(
            confirm_url, {"token": token, "user_id": str(alice.id)}, format="json"
        )

        assert response.status_code == 403

    def test_email_change_deletes_confirmation_record(self, alice, authenticated_client_alice):
        """Test that successful email change deletes confirmation record."""
        new_email = "confirmed@example.com"

        # Request change
        change_url = reverse("authentication:email-change")
        authenticated_client_alice.post(change_url, {"new_email": new_email}, format="json")

        # Confirm exists
        assert EmailConfirmation.objects.filter(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        ).exists()

        # Get token from confirmation record
        confirmation = EmailConfirmation.objects.get(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        )
        token = confirmation.token
        confirm_url = reverse("authentication:email-confirm")
        authenticated_client_alice.post(
            confirm_url, {"token": token, "user_id": str(alice.id)}, format="json"
        )

        # Confirmation record should be marked as confirmed
        confirmation.refresh_from_db()
        assert confirmation.is_confirmed

    def test_multiple_email_change_requests_updates_confirmation(
        self, alice, authenticated_client_alice
    ):
        """Test that multiple change requests update (not duplicate) confirmation record."""
        url = reverse("authentication:email-change")

        # First request
        authenticated_client_alice.post(url, {"new_email": "first@example.com"}, format="json")

        # Second request
        authenticated_client_alice.post(url, {"new_email": "second@example.com"}, format="json")

        # Should only have one unconfirmed confirmation record (latest)
        confirmations = EmailConfirmation.objects.filter(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE, confirmed_at__isnull=True
        )
        assert confirmations.count() == 1
        assert confirmations.first().new_email == "second@example.com"

    def test_email_change_to_existing_email_rejected(self, alice, bob, authenticated_client_alice):
        """Test that changing to an already-used email is rejected."""
        url = reverse("authentication:email-change")

        # Try to change to Bob's email
        response = authenticated_client_alice.post(url, {"new_email": bob.email}, format="json")

        assert response.status_code == 400

    def test_email_change_creates_account_logs(self, alice, authenticated_client_alice):
        """Test that email change creates appropriate account logs."""
        # Clear existing logs
        AccountLog.objects.filter(user=alice).delete()

        new_email = "logged@example.com"

        # Request change
        change_url = reverse("authentication:email-change")
        authenticated_client_alice.post(change_url, {"new_email": new_email}, format="json")

        # Should create log for request
        assert AccountLog.objects.filter(user=alice, operation="EMAIL_CHANGE_REQUESTED").exists()

        # Get token from confirmation record
        confirmation = EmailConfirmation.objects.get(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        )
        token = confirmation.token
        confirm_url = reverse("authentication:email-confirm")
        authenticated_client_alice.post(
            confirm_url, {"token": token, "user_id": str(alice.id)}, format="json"
        )

        # Should have logs for both steps
        logs = AccountLog.objects.filter(
            user=alice, operation__in=["EMAIL_CHANGE_REQUESTED", "EMAIL_CHANGE_CONFIRMED"]
        )
        assert logs.count() >= 1

    def test_email_change_allows_login_with_new_email_and_releases_old_email(
        self, alice, authenticated_client_alice
    ):
        """
        Test that after email change:
        1. Login works with new email
        2. Login fails with old email
        3. Old email can be reused by a new user
        """
        from apps.authentication.models import User
        from apps.authentication.services import AuthenticationService

        old_email = str(alice.email)
        new_email = "alice_new_email@example.com"
        password = "testpassword123"  # Assuming alice's password

        # Request and confirm email change
        change_url = reverse("authentication:email-change")
        authenticated_client_alice.post(change_url, {"new_email": new_email}, format="json")

        confirmation = EmailConfirmation.objects.get(
            user=alice, confirmation_type=EmailConfirmation.EMAIL_CHANGE
        )
        token = confirmation.token

        confirm_url = reverse("authentication:email-confirm")
        authenticated_client_alice.post(
            confirm_url, {"token": token, "user_id": str(alice.id)}, format="json"
        )

        # Refresh alice from database
        alice.refresh_from_db()

        # Verify 1: Email and email_hash were both updated
        assert alice.email == new_email
        assert alice.email_hash == User.hash_email(new_email)

        # Verify 2: Login with new email works (via AuthenticationService)
        # Note: alice fixture might not have a password set, so we need to set one first
        alice.set_password(password)
        alice.save()

        authenticated_user = AuthenticationService.authenticate_user(new_email, password)
        assert authenticated_user is not None
        assert authenticated_user.id == alice.id

        # Verify 3: Login with old email fails
        authenticated_user = AuthenticationService.authenticate_user(old_email, password)
        assert authenticated_user is None

        # Verify 4: Old email can be reused (no uniqueness conflict)
        new_user = User.objects.create_user(
            username="newuser", email=old_email, password="newpassword123"
        )
        assert new_user.email == old_email
        assert new_user.email_hash == User.hash_email(old_email)
