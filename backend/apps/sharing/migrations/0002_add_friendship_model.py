# Generated manually on 2025-11-19

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("sharing", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Friendship",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique friendship identifier",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, help_text="Friendship creation timestamp"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        help_text="User who initiated or maintains this friendship record",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="friendships_initiated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "friend",
                    models.ForeignKey(
                        help_text="The friend user",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="friendships_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Friendship",
                "verbose_name_plural": "Friendships",
                "db_table": "friendships",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["user"], name="idx_friendship_user"),
                    models.Index(fields=["friend"], name="idx_friendship_friend"),
                    models.Index(fields=["user", "friend"], name="idx_friendship_pair"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="friendship",
            constraint=models.UniqueConstraint(fields=("user", "friend"), name="unique_friendship"),
        ),
        migrations.AddConstraint(
            model_name="friendship",
            constraint=models.CheckConstraint(
                check=~models.Q(user=models.F("friend")),
                name="no_self_friendship",
            ),
        ),
    ]
