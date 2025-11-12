# Generated migration for User pseudonym field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0003_user_is_verified_user_verification_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="pseudonym",
            field=models.CharField(
                max_length=100,
                blank=True,
                null=True,
                help_text="User-chosen display name for privacy (unique, case-insensitive)",
            ),
        ),
    ]
