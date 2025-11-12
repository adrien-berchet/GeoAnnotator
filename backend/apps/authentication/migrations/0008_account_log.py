# Generated migration for AccountLog model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0007_email_change_confirmation"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "operation",
                    models.CharField(
                        max_length=50,
                        choices=[
                            ("PSEUDONYM_CHANGED", "Pseudonym Changed"),
                            ("EMAIL_CHANGED", "Email Changed"),
                            ("PASSWORD_CHANGED", "Password Changed"),
                            ("ACCOUNT_DELETED", "Account Deleted"),
                            ("EMAIL_CHANGE_REQUESTED", "Email Change Requested"),
                            ("EMAIL_CHANGE_CONFIRMED", "Email Change Confirmed"),
                        ],
                        help_text="Type of account operation",
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        null=True,
                        help_text="Client IP address",
                    ),
                ),
                (
                    "user_agent",
                    models.CharField(
                        max_length=256,
                        blank=True,
                        null=True,
                        help_text="Client user agent",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="When operation occurred",
                    ),
                ),
                (
                    "details",
                    models.JSONField(
                        blank=True,
                        null=True,
                        help_text="Additional operation-specific data",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="account_logs",
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        help_text="User whose account was modified",
                    ),
                ),
            ],
            options={
                "db_table": "account_logs",
                "verbose_name": "Account Log",
                "verbose_name_plural": "Account Logs",
                "ordering": ["-timestamp"],
            },
        ),
    ]
