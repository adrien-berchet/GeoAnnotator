"""
Management command to clean up duplicate tags (case-insensitive).

This command merges tags that differ only in case, keeping the lowercase version.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.points.models import Tag


class Command(BaseCommand):
    help = "Clean up duplicate tags that differ only in case"

    def handle(self, *args, **options):
        self.stdout.write("Starting tag cleanup...")

        # Get all tags
        all_tags = Tag.objects.all().order_by("name")

        # Group tags by lowercase name
        tags_by_lower = {}
        for tag in all_tags:
            lower_name = tag.name.lower()
            if lower_name not in tags_by_lower:
                tags_by_lower[lower_name] = []
            tags_by_lower[lower_name].append(tag)

        # Find duplicates
        duplicates = {name: tags for name, tags in tags_by_lower.items() if len(tags) > 1}

        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No duplicate tags found."))
            return

        self.stdout.write(f"Found {len(duplicates)} groups of duplicate tags:")
        for name, tags in duplicates.items():
            self.stdout.write(f'  - "{name}": {[t.name for t in tags]}')

        # Merge duplicates
        merged_count = 0
        with transaction.atomic():
            for lower_name, tags in duplicates.items():
                # Keep the tag with lowercase name, or the first one if none is lowercase
                primary_tag = next((t for t in tags if t.name == lower_name), tags[0])

                # If primary tag is not lowercase, update it
                if primary_tag.name != lower_name:
                    primary_tag.name = lower_name
                    primary_tag.save()
                    self.stdout.write(f'  Updated "{tags[0].name}" to "{lower_name}"')

                # Merge all other tags into the primary one
                for tag in tags:
                    if tag.id == primary_tag.id:
                        continue

                    # Move all points from this tag to the primary tag
                    for point in tag.points.all():
                        point.tags.remove(tag)
                        point.tags.add(primary_tag)

                    # Delete the duplicate tag
                    self.stdout.write(f'  Merged "{tag.name}" into "{primary_tag.name}"')
                    tag.delete()
                    merged_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully merged {merged_count} duplicate tags."))
