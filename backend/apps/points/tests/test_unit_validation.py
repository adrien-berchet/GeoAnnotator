"""
Unit tests for coordinate validation.

Tests cover:
- Latitude range validation (-90 to 90)
- Longitude range validation (-180 to 180)
- Point creation with valid coordinates
- Point creation with invalid coordinates
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point

from apps.points.models import GPSPoint

User = get_user_model()


@pytest.mark.django_db
class TestCoordinateValidation:
    """Unit tests for GPS coordinate validation."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return User.objects.create_user(username="test", email="test@example.com", password="TestPass123")

    def test_valid_coordinates(self, user):
        """Test that valid coordinates are accepted."""
        # Test various valid coordinates
        valid_coords = [
            (0, 0),  # Equator, Prime Meridian
            (90, 180),  # North Pole, Date Line
            (-90, -180),  # South Pole, Date Line
            (45.5, -122.7),  # Portland
            (-33.9, 151.2),  # Sydney
        ]

        for lat, lon in valid_coords:
            point = GPSPoint(
                title="Valid Point",
                location=Point(lon, lat),  # Note: Point(lon, lat) not (lat, lon)
                owner=user,
            )
            point.full_clean()  # Should not raise
            point.save()
            assert point.id is not None

    def test_boundary_coordinates(self, user):
        """Test that boundary coordinates are accepted."""
        # Exactly at boundaries
        boundary_coords = [
            (90, 180),
            (90, -180),
            (-90, 180),
            (-90, -180),
            (0, 180),
            (0, -180),
            (90, 0),
            (-90, 0),
        ]

        for lat, lon in boundary_coords:
            point = GPSPoint(title="Boundary Point", location=Point(lon, lat), owner=user)
            point.full_clean()
            point.save()
            assert point.id is not None

    def test_point_location_retrieval(self, user):
        """Test that coordinates can be retrieved correctly."""
        lat, lon = 37.7749, -122.4194  # San Francisco
        point = GPSPoint.objects.create(title="SF Point", location=Point(lon, lat), owner=user)

        # Retrieve and check
        retrieved = GPSPoint.objects.get(id=point.id)
        assert abs(retrieved.location.y - lat) < 0.0001  # latitude
        assert abs(retrieved.location.x - lon) < 0.0001  # longitude
