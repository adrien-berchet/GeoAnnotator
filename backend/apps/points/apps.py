"""
Points app configuration.
"""

from django.apps import AppConfig


class PointsConfig(AppConfig):
    """Points app configuration."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.points'
    verbose_name = 'GPS Points'
