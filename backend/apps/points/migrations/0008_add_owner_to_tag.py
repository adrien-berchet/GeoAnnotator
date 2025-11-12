# Generated manually for restricting tags by user

import django.db.models.deletion
import django.db.models.functions.text
from django.conf import settings
from django.db import migrations
from django.db import models


def assign_tags_to_first_user(apps, schema_editor):
    """
    Assign all existing tags to the first user in the system.
    If no users exist, tags will be deleted.
    """
    Tag = apps.get_model("points", "Tag")
    User = apps.get_model(settings.AUTH_USER_MODEL)

    # Get first user
    first_user = User.objects.first()

    if first_user:
        # Assign all existing tags to first user
        Tag.objects.all().update(owner=first_user)
    else:
        # No users exist, delete all tags
        Tag.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("points", "0007_pointtype_unique_pointtype_name_per_user"),
    ]

    operations = [
        # Remove old unique constraint
        migrations.RemoveConstraint(
            model_name="tag",
            name="unique_tag_name_case_insensitive",
        ),
        # Add owner field (nullable first for data migration)
        migrations.AddField(
            model_name="tag",
            name="owner",
            field=models.ForeignKey(
                null=True,  # Temporarily nullable
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to=settings.AUTH_USER_MODEL,
                help_text="Tag owner",
            ),
        ),
        # Assign existing tags to first user
        migrations.RunPython(assign_tags_to_first_user, reverse_code=migrations.RunPython.noop),
        # Make owner field required
        migrations.AlterField(
            model_name="tag",
            name="owner",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tags",
                to=settings.AUTH_USER_MODEL,
                help_text="Tag owner",
            ),
        ),
        # Add new unique constraint per user
        migrations.AddConstraint(
            model_name="tag",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("name"),
                "owner",
                name="unique_tag_name_per_user",
            ),
        ),
        # Add index on owner
        migrations.AddIndex(
            model_name="tag",
            index=models.Index(fields=["owner"], name="idx_tag_owner"),
        ),
    ]
