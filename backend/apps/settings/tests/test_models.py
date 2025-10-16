"""
Tests for UserPreferences model.
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


@pytest.mark.django_db
class TestUserPreferencesModel:
    """Test cases for UserPreferences model."""

    def test_default_values(self):
        """Test that UserPreferences has correct default values."""
        from apps.settings.models import UserPreferences

        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        # Signal auto-creates preferences, so we retrieve it
        preferences = user.preferences

        assert preferences.language == 'en'
        assert preferences.theme == 'auto'
        assert preferences.export_format == 'geojson'

    def test_one_to_one_relationship(self):
        """Test that User and UserPreferences have one-to-one relationship."""
        from apps.settings.models import UserPreferences

        user = User.objects.create_user(
            email='test2@example.com',
            password='testpass123'
        )
        # Signal auto-creates preferences, so we retrieve it
        preferences = user.preferences

        # Access preferences via user.preferences
        assert user.preferences == preferences
        assert preferences.user == user

        # Cannot create second preferences for same user
        with pytest.raises(Exception):  # IntegrityError
            UserPreferences.objects.create(user=user)

    def test_field_choices_validation(self):
        """Test that invalid choices are rejected."""
        from apps.settings.models import UserPreferences

        user = User.objects.create_user(
            email='test3@example.com',
            password='testpass123'
        )

        # Test invalid theme
        preferences = UserPreferences(user=user, theme='invalid')
        with pytest.raises(ValidationError):
            preferences.full_clean()

        # Test invalid export_format
        preferences = UserPreferences(user=user, export_format='invalid')
        with pytest.raises(ValidationError):
            preferences.full_clean()

    def test_string_representation(self):
        """Test string representation of UserPreferences."""
        from apps.settings.models import UserPreferences

        user = User.objects.create_user(
            email='test4@example.com',
            password='testpass123'
        )
        # Signal auto-creates preferences, so we retrieve it
        preferences = user.preferences

        assert str(preferences) == f"Preferences for {user.email}"

    def test_created_at_updated_at_timestamps(self):
        """Test that created_at and updated_at are set correctly."""
        from apps.settings.models import UserPreferences

        user = User.objects.create_user(
            email='test5@example.com',
            password='testpass123'
        )
        # Signal auto-creates preferences, so we retrieve it
        preferences = user.preferences
