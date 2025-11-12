# Generated migration for database indexes on User, EmailChangeConfirmation, and AccountLog

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0008_account_log"),
    ]

    operations = [
        # Add case-insensitive unique index on pseudonym
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX users_pseudonym_lower_unique ON users (LOWER(pseudonym)) WHERE pseudonym IS NOT NULL;",
            reverse_sql="DROP INDEX IF EXISTS users_pseudonym_lower_unique;",
        ),
        # Add partial index on deleted_at for soft-deleted users
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["deleted_at"],
                name="idx_user_deleted_at",
                condition=models.Q(deleted_at__isnull=False),
            ),
        ),
        # Add index on AccountLog fields
        migrations.AddIndex(
            model_name="accountlog",
            index=models.Index(fields=["user"], name="idx_accountlog_user"),
        ),
        migrations.AddIndex(
            model_name="accountlog",
            index=models.Index(fields=["-timestamp"], name="idx_accountlog_timestamp"),
        ),
        migrations.AddIndex(
            model_name="accountlog",
            index=models.Index(fields=["operation"], name="idx_accountlog_operation"),
        ),
        # Add index on EmailChangeConfirmation expiry for cleanup
        migrations.AddIndex(
            model_name="emailchangeconfirmation",
            index=models.Index(
                fields=["expires_at"],
                name="idx_email_change_expires",
                condition=models.Q(confirmed_at__isnull=True),
            ),
        ),
    ]
