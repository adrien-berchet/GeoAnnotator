# Generated migration

from django.db import migrations


def rename_transfer_to_manage(apps, schema_editor):
    """Rename 'transfer' permission level to 'manage'."""
    Share = apps.get_model('sharing', 'Share')
    Share.objects.filter(permission_level='transfer').update(permission_level='manage')


def rename_manage_to_transfer(apps, schema_editor):
    """Reverse: Rename 'manage' permission level back to 'transfer'."""
    Share = apps.get_model('sharing', 'Share')
    Share.objects.filter(permission_level='manage').update(permission_level='transfer')


class Migration(migrations.Migration):

    dependencies = [
        ('sharing', '0002_add_friendship_model'),
    ]

    operations = [
        migrations.RunPython(
            rename_transfer_to_manage,
            reverse_code=rename_manage_to_transfer,
        ),
    ]
