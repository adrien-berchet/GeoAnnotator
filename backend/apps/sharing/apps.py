"""
Sharing app configuration.
"""

from django.apps import AppConfig


class SharingConfig(AppConfig):
    """Sharing app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sharing"
    verbose_name = "Sharing"
