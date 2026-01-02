"""
Settings app serializers.
"""

from rest_framework import serializers

from .models import UserPreferences


class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer for UserPreferences model.

    Provides read and write operations for user settings.
    Excludes the 'user' field from the API (auto-assigned from request.user).

    Note: The 'theme' model field is exposed as 'theme_mode' in the API
    for consistency with the frontend.
    """

    # Expose 'theme' as 'theme_mode' in the API
    theme_mode = serializers.CharField(source="theme", max_length=10)

    class Meta:
        model = UserPreferences
        fields = [
            "id",
            "language",
            "theme_mode",
            "default_map_type",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_theme_mode(self, value):
        """Validate theme_mode field."""
        valid_themes = dict(UserPreferences.THEME_CHOICES).keys()
        if value not in valid_themes:
            raise serializers.ValidationError(
                f"Invalid theme: {value}. Must be one of: {', '.join(valid_themes)}"
            )
        return value

    def validate_language(self, value):
        """Validate language field."""
        valid_languages = dict(UserPreferences.LANGUAGE_CHOICES).keys()
        if value not in valid_languages:
            raise serializers.ValidationError(
                f"Invalid language: {value}. Must be one of: {', '.join(valid_languages)}"
            )
        return value

    def validate_default_map_type(self, value):
        """Validate default_map_type field."""
        valid_map_types = dict(UserPreferences.MAP_TYPE_CHOICES).keys()
        if value not in valid_map_types:
            raise serializers.ValidationError(
                f"Invalid map type: {value}. Must be one of: {', '.join(valid_map_types)}"
            )
        return value
