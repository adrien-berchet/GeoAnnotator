"""
Admin configuration for settings app.
"""

from django.contrib import admin

from .models import UserPreferences


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Admin interface for UserPreferences model."""

    list_display = [
        "user_email",
        "language",
        "theme",
        "default_map_type",
        "created_at",
        "updated_at",
    ]
    list_filter = ["theme", "default_map_type", "language", "created_at"]
    search_fields = ["user__email"]
    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = (
        ("User", {"fields": ("id", "user")}),
        ("Preferences", {"fields": ("language", "theme", "default_map_type")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(
        description="User Email",
        ordering="user__email",
    )
    def user_email(self, obj):
        """Display user email in list view."""
        return obj.user.email
