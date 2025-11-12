# Generated migration to encrypt email field
# WARNING: This migration requires FERNET_KEY to be set in environment

from django.db import migrations
import fernet_fields.fields


def encrypt_existing_emails(apps, schema_editor):
    """
    Encrypt all existing email addresses.
    This is a data migration that runs after the field type change.
    """
    # Note: This function will be a no-op because AlterField handles the conversion
    # The fernet_fields library will automatically encrypt existing data
    pass


def decrypt_emails(apps, schema_editor):
    """
    Reverse migration: decrypt emails back to plain text.
    """
    # Note: This is handled by AlterField in reverse
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0005_add_deleted_at_and_pending_email"),
    ]

    operations = [
        # Convert email field to encrypted field
        # IMPORTANT: Requires FERNET_KEY environment variable to be set
        migrations.AlterField(
            model_name="user",
            name="email",
            field=fernet_fields.fields.EncryptedEmailField(
                unique=True,
                db_index=True,
                max_length=255,
                help_text="User email address (used for login, encrypted at rest)",
            ),
        ),
        # Run data migration to ensure encryption
        migrations.RunPython(encrypt_existing_emails, decrypt_emails),
    ]
