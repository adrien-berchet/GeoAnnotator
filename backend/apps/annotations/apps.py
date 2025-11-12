"""
Annotations app configuration.
"""

from django.apps import AppConfig


class AnnotationsConfig(AppConfig):
    """Annotations app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.annotations"
    verbose_name = "Annotations"
