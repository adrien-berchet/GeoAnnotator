"""
Pytest configuration and fixtures for points app tests.
"""

import pytest
from apps.authentication.models import User


@pytest.fixture
def alice(db):
    """Create Alice test user."""
    return User.objects.create_user(
        email="alice@example.com",
        password="SecurePass123"
    )


@pytest.fixture
def bob(db):
    """Create Bob test user."""
    return User.objects.create_user(
        email="bob@example.com",
        password="SecurePass456"
    )
