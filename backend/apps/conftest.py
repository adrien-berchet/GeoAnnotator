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
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from apps.annotations.models import Annotation
from apps.authentication.models import User
from apps.points.models import GPSPoint
from apps.points.models import Tag
from apps.trash.models import AnnotationTrash
from apps.trash.models import Trash


@pytest.fixture(autouse=True)
def mock_ratelimit_for_tests(monkeypatch):
    """
    Automatically multiply all rate limits by a large factor during tests.

    This ensures that:
    1. Rate limiting code is actually executed and tested
    2. Tests don't fail due to exceeding rate limits
    3. Production code remains clean without test-specific logic

    The multiplier can be configured via RATE_LIMIT_TESTING_MULTIPLIER setting.
    """
    from apps.core import ratelimit as ratelimit_module

    original_ratelimit = ratelimit_module.ratelimit
    multiplier = getattr(settings, "RATE_LIMIT_TESTING_MULTIPLIER", 10000)

    def ratelimit_with_multiplied_rate(key="ip", rate="5/m", method=None, block=True):
        # Multiply the rate limit for tests
        count, period = rate.split("/")
        adjusted_rate = f"{int(count) * multiplier}/{period}"
        return original_ratelimit(key=key, rate=adjusted_rate, method=method, block=block)

    monkeypatch.setattr(ratelimit_module, "ratelimit", ratelimit_with_multiplied_rate)


def create_verified_user(username: str, email: str, password: str) -> User:
    """
    Helper function to create a verified user for testing.

    Args:
        username: Username for the user
        email: Email address
        password: Password

    Returns:
        Verified User instance
    """
    user = User.objects.create_user(username=username, email=email, password=password)
    user.is_verified = True
    user.save()
    return user


def get_authenticated_client(user: User) -> APIClient:
    """
    Helper function to get an authenticated API client for a user.

    Args:
        user: User instance

    Returns:
        APIClient with authentication credentials set
    """
    api_client = APIClient()
    refresh = RefreshToken.for_user(user)
    token = str(refresh.access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


def login_and_get_token(email: str, password: str, api_client: APIClient = None) -> dict:
    """
    Helper function to login a verified user and get tokens.

    Args:
        email: User email
        password: User password
        api_client: Optional APIClient (creates new one if not provided)

    Returns:
        dict with 'access', 'refresh', 'user' keys

    Raises:
        AssertionError: If login fails
    """
    if api_client is None:
        api_client = APIClient()

    login_url = reverse("authentication:login")
    response = api_client.post(login_url, {"email": email, "password": password}, format="json")

    assert response.status_code == 200, f"Login failed: {response.data}"
    return response.data


@pytest.fixture
def api_client():
    """Provide a clean API client for each test."""
    return APIClient()


@pytest.fixture
def alice(db):
    """Create Alice test user (verified)."""
    user = User.objects.create_user(
        username="alice", email="alice@example.com", password="SecurePass123"
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def bob(db):
    """Create Bob test user (verified)."""
    user = User.objects.create_user(
        username="bob", email="bob@example.com", password="SecurePass456"
    )
    user.is_verified = True
    user.save()
    return user


@pytest.fixture
def charlie(db):
    """Create Charlie test user (verified)."""
    user = User.objects.create_user(
        username="charlie", email="charlie@example.com", password="SecurePass789"
    )
    user.is_verified = True
    user.save()
    return user


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
def text_annotation(gps_point_alice):
    """Create a text annotation for testing."""

    return Annotation.objects.create(
        gps_point=gps_point_alice, type="text", text_content="<p>Test annotation content</p>"
    )


@pytest.fixture
def image_annotation(gps_point_alice, sample_image_file):
    """Create an image annotation for testing."""

    annotation = Annotation.objects.create(
        gps_point=gps_point_alice,
        type="image",
        file=sample_image_file,
        file_name="test_image.jpg",
        file_size=sample_image_file.size,
        mime_type="image/jpeg",
    )
    # Update storage usage
    gps_point_alice.owner.add_storage_usage(sample_image_file.size)
    return annotation


@pytest.fixture
def document_annotation(gps_point_alice, sample_pdf_file):
    """Create a document annotation for testing."""

    annotation = Annotation.objects.create(
        gps_point=gps_point_alice,
        type="document",
        file=sample_pdf_file,
        file_name="test_document.pdf",
        file_size=sample_pdf_file.size,
        mime_type="application/pdf",
    )
    # Update storage usage
    gps_point_alice.owner.add_storage_usage(sample_pdf_file.size)
    return annotation


@pytest.fixture
def gps_point(alice):
    """Generic GPS point fixture (alias for gps_point_alice)."""
    return GPSPoint.objects.create(
        title="Test Point",
        description="<p>Generic test point</p>",
        location=Point(-122.6765, 45.5231),
        owner=alice,
        is_public=False,
    )


@pytest.fixture
def api_request_factory():
    """Provide a request factory for creating mock requests."""
    return APIRequestFactory()


@pytest.fixture
def trash_entry_alice(alice, gps_point_alice):
    """Create a trash entry for Alice's GPS point."""

    trash = Trash.objects.create(gps_point=gps_point_alice, deleted_by=alice)
    return trash


@pytest.fixture
def trash_entry_bob(bob, gps_point_bob):
    """Create a trash entry for Bob's GPS point."""

    trash = Trash.objects.create(gps_point=gps_point_bob, deleted_by=bob)
    return trash


@pytest.fixture
def annotation_trash_entry(alice, text_annotation):
    """Create an annotation trash entry for Alice's annotation."""

    annotation_trash = AnnotationTrash.objects.create(annotation=text_annotation, deleted_by=alice)
    return annotation_trash


@pytest.fixture
def annotation_trash_bob(bob, gps_point_bob):
    """Create an annotation trash entry for Bob's annotation."""

    # Create text annotation for Bob
    annotation = Annotation.objects.create(
        gps_point=gps_point_bob, type="text", text_content="Bob's annotation"
    )
    annotation_trash = AnnotationTrash.objects.create(annotation=annotation, deleted_by=bob)
    return annotation_trash


@pytest.fixture
def gps_point_bob(bob):
    """Create a GPS point owned by Bob."""
    return GPSPoint.objects.create(
        title="Bob's Test Point",
        description="<p>Test point for Bob</p>",
        location=Point(-122.6819, 45.5280),
        owner=bob,
        is_public=False,
    )


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
