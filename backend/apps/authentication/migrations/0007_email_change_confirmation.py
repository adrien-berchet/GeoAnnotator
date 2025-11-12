# Generated migration for EmailChangeConfirmation model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import fernet_fields.fields


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0006_encrypt_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailChangeConfirmation",
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
                    "new_email",
                    fernet_fields.fields.EncryptedEmailField(
                        max_length=255,
                        help_text="Requested new email address",
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        max_length=128,
                        unique=True,
                        help_text="HMAC-based confirmation token",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Token creation timestamp",
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        help_text="Token expiration timestamp (created_at + 30 minutes)",
                    ),
                ),
                (
                    "confirmed_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        help_text="Timestamp when confirmed, NULL if pending",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="email_change_confirmations",
                        to=settings.AUTH_USER_MODEL,
                        help_text="User requesting email change",
                    ),
                ),
            ],
            options={
                "db_table": "email_change_confirmations",
                "verbose_name": "Email Change Confirmation",
                "verbose_name_plural": "Email Change Confirmations",
                "ordering": ["-created_at"],
            },
        ),
    ]
