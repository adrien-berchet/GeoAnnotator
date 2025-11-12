"""
Management command to create missing UserPreferences for existing users.

This command is useful after deploying the settings app to an existing database
where users were created before the UserPreferences signal was in place.

Usage:
    python manage.py create_missing_preferences
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.settings.models import UserPreferences

User = get_user_model()


class Command(BaseCommand):
    help = "Create missing UserPreferences for existing users"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be created without actually creating",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        # Find users without preferences
        users_without_prefs = []
        for user in User.objects.all():
            try:
                UserPreferences.objects.get(user=user)
            except UserPreferences.DoesNotExist:
                users_without_prefs.append(user)

        if not users_without_prefs:
            self.stdout.write(self.style.SUCCESS("All users already have preferences"))
            return

        # Display what will be created
        self.stdout.write(f"Found {len(users_without_prefs)} users without preferences:")
        for user in users_without_prefs:
            self.stdout.write(f"  - {user.email}")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n--dry-run mode: No preferences created"))
            return

        # Create preferences
        created_count = 0
        for user in users_without_prefs:
            UserPreferences.objects.create(user=user)
            created_count += 1
            self.stdout.write(f"Created preferences for {user.email}")

        self.stdout.write(
            self.style.SUCCESS(f"\nSuccessfully created preferences for {created_count} users")
        )
