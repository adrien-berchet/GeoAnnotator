"""
Settings app models.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class UserPreferences(models.Model):
    """
    User preferences model for storing per-user settings.

    Fields:
        - language: Language preference (default: 'en')
        - theme: Theme preference (auto/light/dark, default: 'auto')
        - export_format: Data export format (geojson/kml/csv, default: 'geojson')
    """

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('fr', 'French'),
    ]

    THEME_CHOICES = [
        ('auto', 'Auto'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    EXPORT_FORMAT_CHOICES = [
        ('geojson', 'GeoJSON'),
        ('kml', 'KML'),
        ('csv', 'CSV'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='auto'
    )
    export_format = models.CharField(
        max_length=10,
        choices=EXPORT_FORMAT_CHOICES,
        default='geojson'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = 'User Preferences'
        verbose_name_plural = 'User Preferences'

    def __str__(self):
        return f"Preferences for {self.user.email}"

    def clean(self):
        """Validate model fields."""
        super().clean()

        # Validate language
        if self.language not in dict(self.LANGUAGE_CHOICES):
            raise ValidationError({
                'language': f'Invalid language: {self.language}'
            })

        # Validate theme
        if self.theme not in dict(self.THEME_CHOICES):
            raise ValidationError({
                'theme': f'Invalid theme: {self.theme}'
            })

        # Validate export_format
        if self.export_format not in dict(self.EXPORT_FORMAT_CHOICES):
            raise ValidationError({
                'export_format': f'Invalid export format: {self.export_format}'
            })
