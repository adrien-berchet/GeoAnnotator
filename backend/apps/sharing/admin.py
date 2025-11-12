from django.contrib import admin

from .models import Share


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("gps_point", "owner", "recipient_email", "permission_level", "is_active")
    list_filter = ("permission_level", "is_active")
    search_fields = ("gps_point__title", "owner__email", "recipient_email")
