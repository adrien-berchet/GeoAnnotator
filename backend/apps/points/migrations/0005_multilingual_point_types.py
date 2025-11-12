# Generated migration for multilingual point types
# This migration adds support for multilingual names in PointType model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


def migrate_names_to_multilingual(apps, schema_editor):
    """
    Migrate existing name field to multilingual names field.

    For each PointType:
    - Copy name to names['en']
    - Set creation_language to 'en'
    - Set type_choice to 'base' if user is None, else 'custom'
    - Set visibility to 'public' if user is None, else 'private'
    """
    PointType = apps.get_model("points", "PointType")

    for point_type in PointType.objects.all():
        # Create multilingual names from single name
        point_type.names = {"en": point_type.name}
        point_type.creation_language = "en"

        # Determine type based on user field
        if point_type.user is None:
            point_type.type_choice = "base"
            point_type.visibility = "public"
        else:
            point_type.type_choice = "custom"
            point_type.visibility = "private"

        point_type.save(update_fields=["names", "creation_language", "type_choice", "visibility"])


def reverse_migrate_names(apps, schema_editor):
    """
    Reverse migration: convert multilingual names back to single name.

    Takes the English translation if available, otherwise first available language.
    """
    PointType = apps.get_model("points", "PointType")

    for point_type in PointType.objects.all():
        # Get English name if available, otherwise first available
        if point_type.names:
            if "en" in point_type.names:
                point_type.name = point_type.names["en"]
            else:
                # Get first available name
                first_lang = list(point_type.names.keys())[0]
                point_type.name = point_type.names[first_lang]
        else:
            point_type.name = "Unnamed"

        point_type.save(update_fields=["name"])


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("points", "0004_update_default_icons"),
    ]

    operations = [
        # Step 1: Add new fields (nullable initially for data migration)
        migrations.AddField(
            model_name="pointtype",
            name="names",
            field=models.JSONField(
                default=dict, help_text="Multilingual names (map of language_code: name)"
            ),
        ),
        migrations.AddField(
            model_name="pointtype",
            name="creation_language",
            field=models.CharField(
                default="en", max_length=10, help_text="ISO 639-1 language code at creation"
            ),
        ),
        migrations.AddField(
            model_name="pointtype",
            name="type_choice",
            field=models.CharField(
                max_length=10,
                choices=[("base", "Base"), ("custom", "Custom")],
                default="custom",
                db_column="type",
                help_text="Type classification (base or custom)",
            ),
        ),
        migrations.AddField(
            model_name="pointtype",
            name="visibility",
            field=models.CharField(
                max_length=10,
                choices=[("public", "Public"), ("private", "Private")],
                default="private",
                help_text="Visibility (public or private)",
            ),
        ),
        # Step 2: Migrate data from name to names
        migrations.RunPython(migrate_names_to_multilingual, reverse_migrate_names),
        # Step 3: Remove old constraints that reference 'name' field
        migrations.RemoveConstraint(
            model_name="pointtype",
            name="unique_pointtype_name_per_user",
        ),
        # Step 4: Remove old indexes
        migrations.RemoveIndex(
            model_name="pointtype",
            name="idx_pointtype_user_order",
        ),
        migrations.RemoveIndex(
            model_name="pointtype",
            name="idx_pointtype_user_status",
        ),
        # Step 5: Rename user field to owner (using db_column, so no DB change needed)
        migrations.RenameField(
            model_name="pointtype",
            old_name="user",
            new_name="owner",
        ),
        migrations.AlterField(
            model_name="pointtype",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                db_column="user",
                help_text="Type owner (null for base types)",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="point_types",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # Step 6: Remove old name field
        migrations.RemoveField(
            model_name="pointtype",
            name="name",
        ),
        # Step 7: Update ordering (remove 'name', replace with 'created_at')
        migrations.AlterModelOptions(
            name="pointtype",
            options={
                "ordering": ["order", "created_at"],
                "verbose_name": "Point Type",
                "verbose_name_plural": "Point Types",
            },
        ),
        # Step 8: Add new indexes for owner instead of user
        migrations.AddIndex(
            model_name="pointtype",
            index=models.Index(fields=["owner", "order"], name="idx_pointtype_owner_order"),
        ),
        migrations.AddIndex(
            model_name="pointtype",
            index=models.Index(fields=["owner", "status"], name="idx_pointtype_owner_status"),
        ),
        migrations.AddIndex(
            model_name="pointtype",
            index=models.Index(fields=["type_choice"], name="idx_pointtype_type"),
        ),
    ]
