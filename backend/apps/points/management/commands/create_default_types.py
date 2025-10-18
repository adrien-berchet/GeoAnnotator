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
                'icon': '📍',
                'order': 0,
            },
            {
                'name': 'Restaurant',
                'icon': '🍽️',
                'order': 1,
            },
            {
                'name': 'Hotel',
                'icon': '🏨',
                'order': 2,
            },
            {
                'name': 'Food',
                'icon': '🍔',
                'order': 3,
            },
            {
                'name': 'Water',
                'icon': '💧',
                'order': 4,
            },
            {
                'name': 'Waterfall',
                'icon': '💦',
                'order': 5,
            },
            {
                'name': 'Viewing Point',
                'icon': '👁️',
                'order': 6,
            },
            {
                'name': 'Summit',
                'icon': '⛰️',
                'order': 7,
            },
            {
                'name': 'Starting Point',
                'icon': '🏁',
                'order': 8,
            },
            {
                'name': 'Point of Arrival',
                'icon': '🎯',
                'order': 9,
            },
            {
                'name': 'Point of Entry',
                'icon': '🚪',
                'order': 10,
            },
            {
                'name': 'Parking',
                'icon': '🅿️',
                'order': 11,
            },
            {
                'name': 'Campsite',
                'icon': '⛺',
                'order': 12,
            },
            {
                'name': 'Shelter',
                'icon': '🏠',
                'order': 13,
            },
            {
                'name': 'Danger',
                'icon': '⚠️',
                'order': 14,
            },
            {
                'name': 'Information',
                'icon': 'ℹ️',
                'order': 15,
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
