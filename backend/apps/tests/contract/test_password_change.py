"""
Contract test: POST /api/account/change-password/

Test changing user password.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestPasswordChangeContract:
    """Contract tests for POST /api/account/change-password/ endpoint."""

    def test_change_password_returns_200(self, authenticated_client_alice):
        """
        Test that POST /api/account/change-password/ with valid data returns 200.

        Contract:
        - Status: 200 OK
        - Body: { "detail": "Password changed successfully." }
        - Requires old_password verification
        """
        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "testpass123",  # Default test password
            "new_password": "newSecurePass456!",
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "detail" in response.data
        assert "password changed" in response.data["detail"].lower()

    def test_change_password_incorrect_old_password_returns_400(self, authenticated_client_alice):
        """
        Test that incorrect old password is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Error: "Current password is incorrect."
        """
        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "wrong_password",
            "new_password": "newSecurePass456!",
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "old_password" in response.data
        assert any("incorrect" in str(error).lower() for error in response.data["old_password"])

    def test_change_password_weak_password_returns_400(self, authenticated_client_alice):
        """
        Test that weak password is rejected.

        Contract:
        - Status: 400 BAD REQUEST
        - Minimum 8 characters
        - Not too common
        """
        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "testpass123",
            "new_password": "12345",  # Too short
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data

    def test_change_password_common_password_returns_400(self, authenticated_client_alice):
        """
        Test that too common password is rejected.

        Contract:
        - Django password validation: not too common
        """
        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "testpass123",
            "new_password": "password",  # Too common
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "new_password" in response.data
        assert any("common" in str(error).lower() for error in response.data["new_password"])

    def test_change_password_requires_authentication(self, api_client):
        """
        Test that changing password requires authentication.

        Contract:
        - Status: 401 UNAUTHORIZED for unauthenticated requests
        """
        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "oldpass",
            "new_password": "newpass123",
        }
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_change_password_creates_account_log(self, authenticated_client_alice, user_alice):
        """
        Test that changing password creates AccountLog entry.

        Side effect:
        - Creates AccountLog with operation=PASSWORD_CHANGED
        """
        from apps.authentication.models import AccountLog

        url = reverse("authentication:account-change-password")
        payload = {
            "old_password": "testpass123",
            "new_password": "newSecurePass789!",
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check log entry
        log = AccountLog.objects.filter(user=user_alice, operation="PASSWORD_CHANGED").first()
        assert log is not None

    def test_change_password_actually_updates_password(
        self, authenticated_client_alice, user_alice
    ):
        """
        Test that password is actually updated in database.

        Side effect:
        - Updates User.password with new hashed password
        - Old password no longer works
        """
        url = reverse("authentication:account-change-password")
        new_password = "veryNewPassword999!"
        payload = {
            "old_password": "testpass123",
            "new_password": new_password,
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Refresh user and check password
        user_alice.refresh_from_db()
        assert user_alice.check_password(new_password)
        assert not user_alice.check_password("testpass123")
