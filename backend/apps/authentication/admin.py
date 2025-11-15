from django.contrib import admin

from .models import EmailConfirmation
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "is_verified", "is_active", "is_staff", "date_joined")
    search_fields = ("email", "username")
    list_filter = ("is_verified", "is_active", "is_staff")
    ordering = ("-date_joined",)


@admin.register(EmailConfirmation)
class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "confirmation_type",
        "new_email",
        "created_at",
        "expires_at",
        "confirmed_at",
        "is_expired",
    )
    search_fields = ("user__email", "user__username", "new_email")
    list_filter = ("confirmation_type", "confirmed_at")
    ordering = ("-created_at",)
    readonly_fields = ("token", "new_email_hash", "created_at", "expires_at", "confirmed_at")
