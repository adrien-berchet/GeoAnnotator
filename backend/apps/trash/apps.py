"""
Trash app configuration.
"""

from django.apps import AppConfig


class TrashConfig(AppConfig):
    """Trash app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.trash"
    verbose_name = "Trash"
