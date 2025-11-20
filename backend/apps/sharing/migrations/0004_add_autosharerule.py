# Generated migration for AutoShareRule model

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sharing', '0003_rename_transfer_to_manage'),
        ('points', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoShareRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Unique rule identifier', primary_key=True, serialize=False)),
                ('permission_level', models.CharField(choices=[('view', 'View'), ('edit', 'Edit'), ('manage', 'Manage')], default='view', help_text='Permission level for auto-shared points (view/edit/manage)', max_length=20)),
                ('share_all', models.BooleanField(default=False, help_text='Share all new points (ignores point_types and tags filters)')),
                ('match_all_tags', models.BooleanField(default=True, help_text='Require ALL specified tags to be present (AND logic)')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Rule is active and will be applied to new points')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Rule creation timestamp')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last modification timestamp')),
                ('friend', models.ForeignKey(help_text='Friend who will receive auto-shared points', on_delete=django.db.models.deletion.CASCADE, related_name='auto_share_rules_received', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(help_text='User who owns the points and created the rule', on_delete=django.db.models.deletion.CASCADE, related_name='auto_share_rules', to=settings.AUTH_USER_MODEL)),
                ('point_types', models.ManyToManyField(blank=True, help_text='Point types to match (any match if specified)', related_name='auto_share_rules', to='points.pointtype')),
                ('tags', models.ManyToManyField(blank=True, help_text='Tags to match (ALL must match - AND logic)', related_name='auto_share_rules', to='points.tag')),
            ],
            options={
                'verbose_name': 'Auto Share Rule',
                'verbose_name_plural': 'Auto Share Rules',
                'db_table': 'auto_share_rules',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='autosharerule',
            index=models.Index(fields=['user', 'friend'], name='idx_autoshare_user_friend'),
        ),
        migrations.AddIndex(
            model_name='autosharerule',
            index=models.Index(fields=['user', 'is_active'], name='idx_autoshare_user_active'),
        ),
        migrations.AddIndex(
            model_name='autosharerule',
            index=models.Index(fields=['friend'], name='idx_autoshare_friend'),
        ),
    ]
