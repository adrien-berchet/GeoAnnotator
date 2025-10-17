"""
Management command to create default point types.

Usage: python manage.py create_default_types
"""
from django.core.management.base import BaseCommand
from apps.points.models import PointType


class Command(BaseCommand):
    help = 'Create default point types (base types with user=None)'

    def handle(self, *args, **options):
        """Create default point types."""
        default_types = [
            {
                'name': 'Point',
                'icon': '/icons/default.svg',
                'order': 0,
            },
        ]

        created_count = 0

        for type_data in default_types:
            point_type, created = PointType.objects.get_or_create(
                name=type_data['name'],
                user=None,
                defaults={
                    'icon': type_data['icon'],
                    'order': type_data['order'],
                    'status': 'active',
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created default type: {point_type.name}'
                    )
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Default type already exists: {point_type.name}'
                    )
                )

        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully created {created_count} default type(s)'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\nAll default types already exist'
                )
            )
