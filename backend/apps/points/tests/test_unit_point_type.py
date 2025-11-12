"""
Unit tests for Point model with PointType relationship.

Tests the Point model functionality with type_id including:
- Creating points with types
- Default type assignment
- Type relationship validation
- Switching points to default type when type is deleted
"""

import pytest
from django.contrib.gis.geos import Point as GeoPoint
from django.test import RequestFactory

from apps.points.models import GPSPoint
from apps.points.models import PointType
from apps.points.serializers import CreateGPSPointSerializer


@pytest.mark.unit
class TestPointWithType:
    """Unit tests for GPSPoint model with PointType relationship."""

    def test_create_point_with_type(self, alice):
        """Test creating a point with a specific type."""
        point_type = PointType.objects.create(names={"en": "Restaurant"}, owner=alice, order=1)

        point = GPSPoint.objects.create(
            title="Best Café",
            location=GeoPoint(2.3522, 48.8566),  # Paris
            owner=alice,
            type=point_type,
        )

        assert point.type == point_type
        assert point.type.names == {"en": "Restaurant"}

    def test_create_point_without_type_uses_default(self, alice):
        """Test that creating a point without type assigns default type."""
        # Create default type
        PointType.get_default_type()

        # Use the CreateGPSPointSerializer to create the point with raw data
        data = {
            "title": "Generic Point",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "is_public": True,
        }

        # Simulate a request with RequestFactory
        factory = RequestFactory()
        request = factory.post("/api/points/", data)
        request.user = alice

        serializer = CreateGPSPointSerializer(data=data, context={"request": request})
        assert serializer.is_valid(), serializer.errors
        point = serializer.save()

        # Should have default type assigned
        assert point.type is not None
        assert point.type.names["en"] == "Point"

    def test_point_type_relationship(self, alice):
        """Test the foreign key relationship between Point and PointType."""
        point_type = PointType.objects.create(names={"en": "Museum"}, owner=alice, order=1)

        point1 = GPSPoint.objects.create(
            title="Louvre", location=GeoPoint(2.3364, 48.8606), owner=alice, type=point_type
        )

        point2 = GPSPoint.objects.create(
            title="Orsay", location=GeoPoint(2.3266, 48.8599), owner=alice, type=point_type
        )

        # Check relationship from type to points
        points = GPSPoint.objects.filter(type=point_type)
        assert points.count() == 2
        assert point1 in points
        assert point2 in points

    def test_delete_type_switches_points_to_default(self, alice):
        """Test that deleting a type switches all its points to default type."""
        # Create default type
        default_type = PointType.objects.create(
            names={"en": "Point"},
            owner=None,
            order=0,
            visibility="public",
            type_choice="base",
        )

        # Create custom type
        custom_type = PointType.objects.create(names={"en": "Custom"}, owner=alice, order=1)

        # Create points with custom type
        point1 = GPSPoint.objects.create(
            title="Point 1", location=GeoPoint(2.3522, 48.8566), owner=alice, type=custom_type
        )

        point2 = GPSPoint.objects.create(
            title="Point 2", location=GeoPoint(2.3500, 48.8550), owner=alice, type=custom_type
        )

        # Delete custom type (mark as deleted)
        custom_type.status = "deleted"
        custom_type.save()

        # Points should be switched to default type
        point1.refresh_from_db()
        point2.refresh_from_db()

        assert point1.type == default_type
        assert point2.type == default_type

    def test_user_can_only_assign_own_types(self, alice, bob):
        """Test that a user can only assign their own types to points."""
        bob_type = PointType.objects.create(names={"en": "Bob's Type"}, owner=bob, order=1)

        # Alice shouldn't be able to use Bob's type
        # This validation should happen at the API/service layer
        point = GPSPoint(
            title="Alice's Point", location=GeoPoint(2.3522, 48.8566), owner=alice, type=bob_type
        )

        # The validation logic will be in the serializer/service
        # For now, just test the model allows it (validation elsewhere)
        point.save()
        assert point.type == bob_type

    def test_change_point_type(self, alice):
        """Test changing a point's type."""
        type1 = PointType.objects.create(names={"en": "Type1"}, owner=alice, order=1)
        type2 = PointType.objects.create(names={"en": "Type2"}, owner=alice, order=2)

        point = GPSPoint.objects.create(
            title="Test Point", location=GeoPoint(2.3522, 48.8566), owner=alice, type=type1
        )

        assert point.type == type1

        # Change type
        point.type = type2
        point.save()

        point.refresh_from_db()
        assert point.type == type2

    def test_multiple_points_same_type(self, alice):
        """Test that multiple points can share the same type."""
        point_type = PointType.objects.create(names={"en": "Restaurant"}, owner=alice, order=1)

        points = []
        for i in range(5):
            point = GPSPoint.objects.create(
                title=f"Restaurant {i}",
                location=GeoPoint(2.35 + i * 0.01, 48.85 + i * 0.01),
                owner=alice,
                type=point_type,
            )
            points.append(point)

        # All points should have the same type
        for point in points:
            assert point.type == point_type

        # Type should have 5 points
        assert GPSPoint.objects.filter(type=point_type).count() == 5

    def test_type_deleted_status_not_cascade(self, alice):
        """Test that deleting type doesn't cascade delete points."""
        point_type = PointType.objects.create(names={"en": "ToDelete"}, owner=alice, order=1)

        point = GPSPoint.objects.create(
            title="Point", location=GeoPoint(2.3522, 48.8566), owner=alice, type=point_type
        )

        # Soft delete the type
        point_type.status = "deleted"
        point_type.save()

        # Point should still exist
        assert GPSPoint.objects.filter(id=point.id).exists()

    def test_base_type_can_be_used_by_all_users(self, alice, bob):
        """Test that base types (owner=None) can be used by all users."""
        base_type = PointType.objects.create(
            names={"en": "Point"},
            owner=None,
            order=0,
            visibility="public",
            type_choice="base",
        )

        point_alice = GPSPoint.objects.create(
            title="Alice's Point", location=GeoPoint(2.3522, 48.8566), owner=alice, type=base_type
        )

        point_bob = GPSPoint.objects.create(
            title="Bob's Point", location=GeoPoint(2.3500, 48.8550), owner=bob, type=base_type
        )

        assert point_alice.type == base_type
        assert point_bob.type == base_type
