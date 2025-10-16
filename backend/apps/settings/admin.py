"""
Admin configuration for settings app.
"""
from django.contrib import admin
from .models import UserPreferences


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """Admin interface for UserPreferences model."""

    list_display = [
        'user_email',
        'language',
        'theme',
        'export_format',
        'created_at',
        'updated_at'
    ]
    list_filter = ['theme', 'export_format', 'language', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('id', 'user')
        }),
        ('Preferences', {
            'fields': ('language', 'theme', 'export_format')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email in list view."""
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
