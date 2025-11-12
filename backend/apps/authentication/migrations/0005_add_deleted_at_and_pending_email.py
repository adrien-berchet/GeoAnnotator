# Generated migration for User soft delete and email change fields

from django.db import migrations, models
import fernet_fields.fields


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0004_add_pseudonym"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="deleted_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Soft delete timestamp, NULL for active users",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="pending_email",
            field=fernet_fields.fields.EncryptedEmailField(
                blank=True,
                null=True,
                max_length=255,
                help_text="Temporary storage for unconfirmed email changes",
            ),
        ),
    ]
