"""
Contract test: Create a custom point type.

Test the POST /api/point-types/ endpoint contract.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestCreatePointTypeContract:
    """Contract tests for creating point types."""

    def test_create_point_type_returns_201_with_object(self, authenticated_client_alice):
        """
        Test that POST /api/point-types/ returns 201 with created object.

        Contract:
        - Status: 201 CREATED
        - Body: Created point type object
        - Request: names (map), creation_language (string), visibility (string)
        """
        url = reverse("point-types:list")
        payload = {"names": {"en": "Tree"}, "creation_language": "en", "visibility": "private"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert isinstance(response.data, dict)

    def test_create_point_type_response_schema(self, authenticated_client_alice):
        """
        Test that created point type has the correct schema.

        Contract:
        - id: string (UUID)
        - type: "custom" (always custom for user-created types)
        - names: object matching request
        - creation_language: string matching request
        - owner: string (current user UUID)
        - visibility: string matching request
        """
        url = reverse("point-types:list")
        payload = {"names": {"en": "Landmark"}, "creation_language": "en", "visibility": "public"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Check response schema
        assert "id" in response.data
        assert "type" in response.data
        assert "names" in response.data
        assert "creation_language" in response.data
        assert "owner" in response.data
        assert "visibility" in response.data

        # Check values
        assert isinstance(response.data["id"], str)
        assert response.data["type"] == "custom"
        assert response.data["names"] == {"en": "Landmark"}
        assert response.data["creation_language"] == "en"
        assert response.data["owner"] is not None
        assert response.data["visibility"] == "public"

    def test_create_point_type_with_multiple_translations(self, authenticated_client_alice):
        """Test creating a point type with multiple language translations."""
        url = reverse("point-types:list")
        payload = {
            "names": {"en": "Mountain", "fr": "Montagne"},
            "creation_language": "en",
            "visibility": "private",
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["names"]["en"] == "Mountain"
        assert response.data["names"]["fr"] == "Montagne"

    def test_create_point_type_requires_authentication(self, api_client):
        """Test that creating a point type requires authentication."""
        url = reverse("point-types:list")
        payload = {"names": {"en": "Tree"}, "creation_language": "en", "visibility": "private"}
        response = api_client.post(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_point_type_requires_names(self, authenticated_client_alice):
        """Test that names field is required."""
        url = reverse("point-types:list")
        payload = {"creation_language": "en", "visibility": "private"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_point_type_requires_at_least_one_name(self, authenticated_client_alice):
        """Test that at least one name is required."""
        url = reverse("point-types:list")
        payload = {"names": {}, "creation_language": "en", "visibility": "private"}
        response = authenticated_client_alice.post(url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
