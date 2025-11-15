# Generated manually for email confirmation consolidation

import fernet_fields.fields
from django.db import migrations
from django.db import models


def migrate_email_change_confirmations(apps, schema_editor):
    """Migrate existing EmailChangeConfirmation records to EmailConfirmation."""
    EmailChangeConfirmation = apps.get_model("authentication", "EmailChangeConfirmation")
    EmailConfirmation = apps.get_model("authentication", "EmailConfirmation")

    for old_confirmation in EmailChangeConfirmation.objects.all():
        EmailConfirmation.objects.create(
            user=old_confirmation.user,
            confirmation_type="email_change",
            token=old_confirmation.token,
            new_email=old_confirmation.new_email,
            new_email_hash=old_confirmation.new_email_hash,
            created_at=old_confirmation.created_at,
            expires_at=old_confirmation.expires_at,
            confirmed_at=old_confirmation.confirmed_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_emailconfirmation_and_update_accountlog"),
    ]

    operations = [
        # Add new fields to EmailConfirmation
        migrations.AddField(
            model_name="emailconfirmation",
            name="confirmation_type",
            field=models.CharField(
                choices=[("registration", "Registration"), ("email_change", "Email Change")],
                default="registration",
                help_text="Type of email confirmation",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="emailconfirmation",
            name="new_email",
            field=fernet_fields.fields.EncryptedEmailField(
                blank=True,
                help_text="New email address (only for email change confirmations)",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="emailconfirmation",
            name="new_email_hash",
            field=models.CharField(
                blank=True,
                help_text="SHA-256 hash of new email for uniqueness check",
                max_length=64,
            ),
        ),
        # Add indexes for performance
        migrations.AddIndex(
            model_name="emailconfirmation",
            index=models.Index(fields=["confirmation_type"], name="idx_confirmation_type"),
        ),
        migrations.AddIndex(
            model_name="emailconfirmation",
            index=models.Index(fields=["user", "confirmation_type"], name="idx_user_conf_type"),
        ),
        # Migrate data from EmailChangeConfirmation to EmailConfirmation
        migrations.RunPython(migrate_email_change_confirmations, migrations.RunPython.noop),
        # Remove old EmailChangeConfirmation model
        migrations.DeleteModel(
            name="EmailChangeConfirmation",
        ),
    ]
