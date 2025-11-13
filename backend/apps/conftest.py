"""
Pytest configuration and shared fixtures for tests.

This module provides common fixtures and configuration for all tests.
"""

import shutil
from io import BytesIO

import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User
from apps.points.models import GPSPoint
from apps.points.models import Tag


@pytest.fixture
def api_client():
    """Provide a clean API client for each test."""
    return APIClient()


@pytest.fixture
def alice(db):
    """Create Alice test user."""
    return User.objects.create_user(username="alice", email="alice@example.com", password="SecurePass123")


@pytest.fixture
def bob(db):
    """Create Bob test user."""
    return User.objects.create_user(username="bob", email="bob@example.com", password="SecurePass456")


@pytest.fixture
def charlie(db):
    """Create Charlie test user."""
    return User.objects.create_user(username="charlie", email="charlie@example.com", password="SecurePass789")


@pytest.fixture
def authenticated_client_alice(alice):
    """Provide an authenticated API client for Alice."""
    api_client = APIClient()

    # Generate JWT token manually (bypass login endpoint to avoid rate limiting)
    refresh = RefreshToken.for_user(alice)
    token = str(refresh.access_token)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def authenticated_client_bob(bob):
    """Provide an authenticated API client for Bob."""
    api_client = APIClient()

    # Generate JWT token manually (bypass login endpoint to avoid rate limiting)
    refresh = RefreshToken.for_user(bob)
    token = str(refresh.access_token)

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def gps_point_alice(alice):
    """Create a GPS point owned by Alice."""
    return GPSPoint.objects.create(
        title="Alice's Test Point",
        description="<p>Test point for integration tests</p>",
        location=Point(-122.6765, 45.5231),  # Portland, OR
        owner=alice,
        is_public=False,
    )


@pytest.fixture
def public_gps_point_alice(alice):
    """Create a public GPS point owned by Alice."""
    return GPSPoint.objects.create(
        title="Alice's Public Point",
        description="<p>Public test point</p>",
        location=Point(-122.7095, 45.5195),  # Portland Japanese Garden
        owner=alice,
        is_public=True,
    )


@pytest.fixture
def tag_fishing(db, alice):
    """Create 'fishing' tag for alice."""
    return Tag.objects.get_or_create(name="fishing", owner=alice)[0]


@pytest.fixture
def tag_hiking(db, alice):
    """Create 'hiking' tag for alice."""
    return Tag.objects.get_or_create(name="hiking", owner=alice)[0]


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing."""
    image = Image.new("RGB", (100, 100), color="red")
    image_io = BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)

    return SimpleUploadedFile("test_image.jpg", image_io.read(), content_type="image/jpeg")


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + (b"0" * 1000)

    return SimpleUploadedFile("test_document.pdf", pdf_content, content_type="application/pdf")


@pytest.fixture
def sample_geojson():
    """Create a sample GeoJSON structure for testing."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-122.6765, 45.5231]},
                "properties": {"title": "Test Point", "description": "Test import"},
            }
        ],
    }


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content for testing."""
    return """latitude,longitude,title,description,tags
45.5231,-122.6765,"Point 1","Description 1","tag1|tag2"
45.5195,-122.7095,"Point 2","Description 2","tag3"
"""


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.

    This fixture is autouse=True, so it runs for every test.
    It ensures that the database is available.
    """
    pass


@pytest.fixture
def clear_media_files():
    """Clean up media files after tests."""
    yield

    # Cleanup media files after test
    media_root = settings.MEDIA_ROOT
    if media_root.exists():
        for item in media_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
