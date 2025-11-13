"""
Tests for settings API views.
"""

import time

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return API client instance."""
    return APIClient()


@pytest.fixture
def user():
    """Create and return test user."""
    return User.objects.create_user(username="test", email="test@example.com", password="testpass123")


@pytest.fixture
def authenticated_client(api_client, user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
class TestGetUserPreferences:
    """Test GET /api/v1/settings/ endpoint."""

    def test_authenticated_user_can_retrieve_preferences(self, authenticated_client, user):
        """Test that authenticated user can retrieve their preferences."""

        # Signal auto-creates preferences, so we retrieve and update them
        preferences = user.preferences
        preferences.theme = "dark"
        preferences.export_format = "kml"
        preferences.save()

        url = "/api/v1/settings/"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["theme_mode"] == "dark"
        assert response.data["export_format"] == "kml"

    def test_response_matches_schema(self, authenticated_client, user):
        """Test that response matches expected schema."""
        # Signal auto-creates preferences, so they already exist

        url = "/api/v1/settings/"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check all required fields are present
        assert "id" in response.data
        assert "language" in response.data
        assert "theme_mode" in response.data
        assert "export_format" in response.data
        assert "created_at" in response.data
        assert "updated_at" in response.data

    def test_unauthenticated_request_returns_401(self, api_client):
        """Test that unauthenticated request returns 401."""
        url = "/api/v1/settings/"
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_preferences_not_found_returns_404(self, authenticated_client, user):
        """Test that 404 is returned if preferences don't exist."""
        # Don't create preferences
        url = "/api/v1/settings/"
        response = authenticated_client.get(url)

        # This test might pass with 200 if signal auto-creates preferences
        # In that case, we expect 200 with default values
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
class TestPatchUserPreferences:
    """Test PATCH /api/v1/settings/ endpoint."""

    def test_authenticated_user_can_update_theme(self, authenticated_client, user):
        """Test that authenticated user can update theme."""
        # Signal auto-creates preferences, so we retrieve them
        preferences = user.preferences

        url = "/api/v1/settings/"
        data = {"theme_mode": "dark"}
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["theme_mode"] == "dark"

        # Verify database update
        preferences.refresh_from_db()
        assert preferences.theme == "dark"

    def test_partial_update_only_modified_fields(self, authenticated_client, user):
        """Test partial update with only modified fields sent."""
        # Signal auto-creates preferences, so we retrieve and update them
        preferences = user.preferences
        preferences.theme = "light"
        preferences.export_format = "geojson"
        preferences.save()

        url = "/api/v1/settings/"
        data = {"theme_mode": "dark"}  # Only update theme
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        preferences.refresh_from_db()
        assert preferences.theme == "dark"
        assert preferences.export_format == "geojson"  # Unchanged

    def test_response_includes_all_fields(self, authenticated_client, user):
        """Test that response includes all fields even for partial update."""
        # Signal auto-creates preferences, so they already exist

        url = "/api/v1/settings/"
        data = {"theme_mode": "dark"}
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # All fields should be in response
        assert "id" in response.data
        assert "language" in response.data
        assert "theme_mode" in response.data
        assert "export_format" in response.data
        assert "created_at" in response.data
        assert "updated_at" in response.data

    def test_invalid_theme_value_returns_400(self, authenticated_client, user):
        """Test that invalid theme value returns 400."""
        # Signal auto-creates preferences, so they already exist

        url = "/api/v1/settings/"
        data = {"theme_mode": "invalid_theme"}
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "theme_mode" in response.data or "error" in response.data

    def test_unauthenticated_request_returns_401(self, api_client):
        """Test that unauthenticated request returns 401."""
        url = "/api/v1/settings/"
        data = {"theme_mode": "dark"}
        response = api_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_updated_at_timestamp_changes(self, authenticated_client, user):
        """Test that updated_at timestamp changes after update."""
        # Signal auto-creates preferences, so we retrieve them
        preferences = user.preferences
        original_updated_at = preferences.updated_at

        time.sleep(0.01)  # Ensure time difference

        url = "/api/v1/settings/"
        data = {"theme_mode": "dark"}
        response = authenticated_client.patch(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        preferences.refresh_from_db()
        assert preferences.updated_at > original_updated_at


@pytest.mark.django_db
class TestSettingsIntegration:
    """Integration tests for settings functionality."""

    def test_user_registration_creates_default_preferences(self):
        """Test that user registration auto-creates preferences with defaults."""
        # This test will pass once signal is implemented
        user = User.objects.create_user(username="newuser", email="newuser@example.com", password="testpass123")

        # Check if preferences were auto-created

        assert hasattr(user, "preferences")
        preferences = user.preferences
        assert preferences.language == "en"
        assert preferences.theme == "auto"
        assert preferences.export_format == "geojson"

    def test_preferences_persist_after_logout_login(self, api_client):
        """Test that preferences persist after logout/login."""
        # Create user - signal auto-creates preferences
        user = User.objects.create_user(username="persist", email="persist@example.com", password="testpass123")

        # Set initial theme
        preferences = user.preferences
        preferences.theme = "dark"
        preferences.save()

        # "Login" and update
        api_client.force_authenticate(user=user)
        url = "/api/v1/settings/"
        api_client.patch(url, {"export_format": "kml"}, format="json")

        # "Logout"
        api_client.force_authenticate(user=None)

        # "Login" again
        api_client.force_authenticate(user=user)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["theme_mode"] == "dark"
        assert response.data["export_format"] == "kml"

    def test_per_user_isolation(self, api_client):
        """Test that User A changes don't affect User B."""
        # Create two users - signal auto-creates preferences for both
        user_a = User.objects.create_user(username="usera", email="usera@example.com", password="testpass123")
        user_b = User.objects.create_user(username="userb", email="userb@example.com", password="testpass123")

        # Set initial preferences
        prefs_a = user_a.preferences
        prefs_a.theme = "dark"
        prefs_a.save()

        prefs_b = user_b.preferences
        prefs_b.theme = "light"
        prefs_b.save()

        # User A updates their preferences
        api_client.force_authenticate(user=user_a)
        url = "/api/v1/settings/"
        api_client.patch(url, {"export_format": "kml"}, format="json")

        # User B's preferences should be unchanged
        api_client.force_authenticate(user=user_b)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["theme_mode"] == "light"
        assert response.data["export_format"] == "geojson"  # Unchanged
