# Generated manually for email confirmation feature

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


def mark_existing_users_as_verified(apps, schema_editor):
    """Mark all existing users as verified to avoid breaking existing accounts."""
    User = apps.get_model("authentication", "User")
    User.objects.filter(is_verified=False).update(is_verified=True)


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        # Create EmailConfirmation model
        migrations.CreateModel(
            name="EmailConfirmation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        help_text="HMAC-based confirmation token", max_length=128, unique=True
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, help_text="Token creation timestamp"),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        help_text="Token expiration timestamp (created_at + 48 hours)"
                    ),
                ),
                (
                    "confirmed_at",
                    models.DateTimeField(
                        blank=True, help_text="Timestamp when confirmed, NULL if pending", null=True
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User confirming their email",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_confirmations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Email Confirmation",
                "verbose_name_plural": "Email Confirmations",
                "db_table": "email_confirmations",
                "ordering": ["-created_at"],
            },
        ),
        # Update AccountLog choices to include new operation types
        migrations.AlterField(
            model_name="accountlog",
            name="operation",
            field=models.CharField(
                choices=[
                    ("USERNAME_CHANGED", "Username Changed"),
                    ("EMAIL_CHANGED", "Email Changed"),
                    ("PASSWORD_CHANGED", "Password Changed"),
                    ("ACCOUNT_DELETED", "Account Deleted"),
                    ("EMAIL_CHANGE_REQUESTED", "Email Change Requested"),
                    ("EMAIL_CHANGE_CONFIRMED", "Email Change Confirmed"),
                    ("EMAIL_CONFIRMED", "Email Confirmed"),
                    ("CONFIRMATION_EMAIL_RESENT", "Confirmation Email Resent"),
                ],
                help_text="Type of account operation",
                max_length=50,
            ),
        ),
        # Mark all existing users as verified (backwards compatibility)
        migrations.RunPython(mark_existing_users_as_verified, migrations.RunPython.noop),
    ]
