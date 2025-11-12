"""
Settings app configuration.
"""

from django.apps import AppConfig


class SettingsConfig(AppConfig):
    """Configuration for the settings app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.settings"
    verbose_name = "User Settings"

    def ready(self):
        """Import signals when app is ready."""
        import apps.settings.signals  # noqa: F401
