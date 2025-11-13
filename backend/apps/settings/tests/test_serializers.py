"""
Tests for UserPreferences serializer.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserPreferencesSerializer:
    """Test cases for UserPreferencesSerializer."""

    def test_serialization(self):
        """Test that UserPreferences instance is serialized correctly."""
        from apps.settings.serializers import UserPreferencesSerializer

        user = User.objects.create_user(username="test", email="test@example.com", password="testpass123")
        # Signal auto-creates preferences, so we retrieve and update it
        preferences = user.preferences
        preferences.theme = "dark"
        preferences.export_format = "kml"
        preferences.save()

        serializer = UserPreferencesSerializer(preferences)
        data = serializer.data

        assert "id" in data
        assert data["language"] == "en"
        assert data["theme_mode"] == "dark"
        assert data["export_format"] == "kml"
        assert "created_at" in data
        assert "updated_at" in data

    def test_deserialization_with_valid_data(self):
        """Test deserialization with valid data."""
        from apps.settings.serializers import UserPreferencesSerializer

        data = {"language": "en", "theme_mode": "light", "export_format": "csv"}

        serializer = UserPreferencesSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data["theme"] == "light"
        assert serializer.validated_data["export_format"] == "csv"

    def test_validation_invalid_theme_choice(self):
        """Test that invalid theme choice is rejected."""
        from apps.settings.serializers import UserPreferencesSerializer

        data = {"theme_mode": "invalid_theme"}

        serializer = UserPreferencesSerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert "theme_mode" in serializer.errors

    def test_validation_invalid_export_format_choice(self):
        """Test that invalid export_format choice is rejected."""
        from apps.settings.serializers import UserPreferencesSerializer

        data = {"export_format": "invalid_format"}

        serializer = UserPreferencesSerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert "export_format" in serializer.errors

    def test_partial_update(self):
        """Test partial update with only theme field."""
        from apps.settings.serializers import UserPreferencesSerializer

        user = User.objects.create_user(username="test2", email="test2@example.com", password="testpass123")
        # Signal auto-creates preferences, so we retrieve it
        preferences = user.preferences

        # Update only theme
        data = {"theme_mode": "dark"}
        serializer = UserPreferencesSerializer(preferences, data=data, partial=True)

        assert serializer.is_valid()
        updated_preferences = serializer.save()

        assert updated_preferences.theme == "dark"
        assert updated_preferences.language == "en"  # Unchanged
        assert updated_preferences.export_format == "geojson"  # Unchanged
