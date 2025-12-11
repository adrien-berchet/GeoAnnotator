"""
Settings app models.
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

User = get_user_model()


class UserPreferences(models.Model):
    """
    User preferences model for storing per-user settings.

    Fields:
        - language: Language preference (default: 'en')
        - theme: Theme preference (auto/light/dark, default: 'auto')
        - default_map_type: Default map type (osm/satellite/topo/cycle, default: 'osm')
    """

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("fr", "French"),
    ]

    THEME_CHOICES = [
        ("auto", "Auto"),
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    MAP_TYPE_CHOICES = [
        ("osm", "Street Map"),
        ("satellite", "Satellite"),
        ("topo", "Topographic"),
        ("cycle", "Cycle Map"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default="en")
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="auto")
    default_map_type = models.CharField(max_length=20, choices=MAP_TYPE_CHOICES, default="osm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_preferences"
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user.email}"

    def clean(self):
        """Validate model fields."""
        super().clean()

        # Validate language
        if self.language not in dict(self.LANGUAGE_CHOICES):
            raise ValidationError({"language": f"Invalid language: {self.language}"})

        # Validate theme
        if self.theme not in dict(self.THEME_CHOICES):
            raise ValidationError({"theme": f"Invalid theme: {self.theme}"})

        # Validate default_map_type
        if self.default_map_type not in dict(self.MAP_TYPE_CHOICES):
            raise ValidationError(
                {"default_map_type": f"Invalid map type: {self.default_map_type}"}
            )
