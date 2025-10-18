# Generated migration for updating default point type icons

from django.db import migrations, models


def update_default_icons(apps, schema_editor):
    """Update icon field default and existing /icons/default.svg to emoji."""
    PointType = apps.get_model('points', 'PointType')

    # Update all types with the old default icon to the new emoji
    PointType.objects.filter(icon='/icons/default.svg').update(icon='📍')


def reverse_update_icons(apps, schema_editor):
    """Reverse migration - update emoji icons back to SVG."""
    PointType = apps.get_model('points', 'PointType')

    # Update all types with emoji to the old default
    PointType.objects.filter(icon='📍').update(icon='/icons/default.svg')


class Migration(migrations.Migration):

    dependencies = [
        ('points', '0003_usertypeorder_usertypeorder_unique_user_type_order'),
    ]

    operations = [
        # First, run the data migration to update existing records
        migrations.RunPython(update_default_icons, reverse_update_icons),

        # Then, alter the field to change the default value
        migrations.AlterField(
            model_name='pointtype',
            name='icon',
            field=models.CharField(
                default='📍',
                help_text='Icon URL, emoji, or asset reference',
                max_length=500,
            ),
        ),
    ]
