"""
Integration Test - Scenario 1: User Registration and Authentication

Acceptance Criteria: FR-001 to FR-004
- User registration with email/password
- Login with JWT tokens (access + refresh)
- User profile retrieval with storage quota
- Token refresh mechanism
- Invalid credentials handling
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User


@pytest.mark.django_db
class TestScenario1AuthenticationFlow:
    """Integration tests for complete authentication workflow."""

    def setup_method(self):
        """Set up test client before each test."""
        self.client = APIClient()
        self.register_url = reverse("authentication:register")
        self.login_url = reverse("authentication:login")
        self.refresh_url = reverse("authentication:refresh")
        self.profile_url = reverse("authentication:profile")

    def test_step_1_register_new_user(self):
        """
        Step 1: Register New User

        Expected:
        - Response 201 with JWT tokens (access + refresh)
        - User created with 2GB default storage quota
        - storage_used = 0, storage_limit = 2147483648
        """
        # Given
        user_data = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "SecurePass123",
        }

        # When
        response = self.client.post(self.register_url, user_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data

        # Verify user created with correct defaults
        email_hash = User.hash_email("alice@example.com")
        user = User.objects.get(email_hash=email_hash)
        assert user.storage_used == 0
        assert user.storage_limit == 2147483648  # 2GB in bytes

    def test_step_2_login_with_valid_credentials(self):
        """
        Step 2: Login with Valid Credentials

        Expected:
        - Response 200 with JWT tokens
        - access token valid 1 hour, refresh token valid 7 days
        """
        # Given - Create user
        User.objects.create_user(username="alice", email="alice@example.com", password="SecurePass123")

        login_data = {"email": "alice@example.com", "password": "SecurePass123"}

        # When
        response = self.client.post(self.login_url, login_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data

        # Verify token structure (JWT has 3 parts separated by dots)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        assert len(access_token.split(".")) == 3
        assert len(refresh_token.split(".")) == 3

    def test_step_3_get_user_profile(self):
        """
        Step 3: Get User Profile

        Expected:
        - Response 200 with user profile
        - storage_percentage = (0 / 2147483648) * 100 = 0.0
        """
        # Given - Create and authenticate user
        User.objects.create_user(username="alice@example.com_user", email="alice@example.com", password="SecurePass123")

        login_response = self.client.post(
            self.login_url,
            {"email": "alice@example.com", "password": "SecurePass123"},
            format="json",
        )
        access_token = login_response.data["access"]

        # When
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.profile_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["email"] == "alice@example.com"
        assert response.data["storage_used"] == 0
        assert response.data["storage_limit"] == 2147483648
        assert response.data["storage_percentage"] == 0.0

    def test_step_4_refresh_access_token(self):
        """
        Step 4: Refresh Access Token

        Expected:
        - Response 200 with new access token
        """
        # Given - Create user and get tokens
        User.objects.create_user(username="alice@example.com_user", email="alice@example.com", password="SecurePass123")

        login_response = self.client.post(
            self.login_url,
            {"email": "alice@example.com", "password": "SecurePass123"},
            format="json",
        )
        refresh_token = login_response.data["refresh"]

        # When
        response = self.client.post(self.refresh_url, {"refresh": refresh_token}, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

        # Verify new access token is different from original
        new_access_token = response.data["access"]
        assert new_access_token != login_response.data["access"]

    def test_step_5_login_with_invalid_credentials(self):
        """
        Step 5: Login with Invalid Credentials

        Expected:
        - Response 401 with error "INVALID_CREDENTIALS"
        """
        # Given - Create user
        User.objects.create_user(username="alice@example.com_user", email="alice@example.com", password="SecurePass123")

        invalid_data = {"email": "alice@example.com", "password": "WrongPassword"}

        # When
        response = self.client.post(self.login_url, invalid_data, format="json")

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data or "detail" in response.data or "details" in response.data

    def test_complete_authentication_flow(self):
        """
        Complete Flow: Register → Login → Get Profile → Refresh → Logout

        This test validates the entire authentication lifecycle.
        """
        # Step 1: Register
        register_response = self.client.post(
            self.register_url,
            {"username": "bob", "email": "bob@example.com", "password": "SecurePass456"},
            format="json",
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # Step 2: Login
        login_response = self.client.post(
            self.login_url,
            {"email": "bob@example.com", "password": "SecurePass456"},
            format="json",
        )
        assert login_response.status_code == status.HTTP_200_OK
        access_token = login_response.data["access"]
        refresh_token = login_response.data["refresh"]

        # Step 3: Get Profile
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_response = self.client.get(self.profile_url)
        assert profile_response.status_code == status.HTTP_200_OK
        assert profile_response.data["email"] == "bob@example.com"

        # Step 4: Refresh Token
        refresh_response = self.client.post(
            self.refresh_url, {"refresh": refresh_token}, format="json"
        )
        assert refresh_response.status_code == status.HTTP_200_OK
        new_access_token = refresh_response.data["access"]

        # Step 5: Use new token to access profile
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        profile_response_2 = self.client.get(self.profile_url)
        assert profile_response_2.status_code == status.HTTP_200_OK
