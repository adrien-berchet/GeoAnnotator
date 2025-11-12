"""
Sharing app configuration.
"""

from django.apps import AppConfig


class SharingConfig(AppConfig):
    """Sharing app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sharing"
    verbose_name = "Sharing"

    def ready(self):
        """Import signals when the app is ready."""
        import apps.sharing.signals  # noqa: F401
