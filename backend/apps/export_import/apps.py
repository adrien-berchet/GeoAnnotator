"""
Export/Import app configuration.
"""

from django.apps import AppConfig


class ExportImportConfig(AppConfig):
    """Export/Import app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.export_import"
    verbose_name = "Export/Import"
