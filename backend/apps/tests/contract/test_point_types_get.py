"""
Contract test: Get a point type by ID.

Test the GET /api/point-types/{id}/ endpoint contract.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestGetPointTypeContract:
    """Contract tests for retrieving a single point type."""

    def test_get_point_type_returns_200_with_object(self, authenticated_client_alice):
        """
        Test that GET /api/point-types/{id}/ returns 200 with object.

        Contract:
        - Status: 200 OK
        - Body: Point type object
        """
        # First create a point type
        url_list = reverse("point-types:list")
        payload = {"names": {"en": "Forest"}, "creation_language": "en", "visibility": "private"}
        create_response = authenticated_client_alice.post(url_list, payload, format="json")
        point_type_id = create_response.data["id"]

        # Now get the point type
        url_detail = reverse("point-types:detail", args=[point_type_id])
        response = authenticated_client_alice.get(url_detail)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_get_point_type_response_schema(self, authenticated_client_alice):
        """
        Test that retrieved point type has the correct schema.

        Contract:
        - id: string (UUID)
        - type: string (enum: base, custom)
        - names: object (map of language_code: name)
        - creation_language: string (ISO 639-1 code)
        - owner: string or null
        - visibility: string (enum: public, private)
        """
        # First create a point type
        url_list = reverse("point-types:list")
        payload = {
            "names": {"en": "River", "fr": "Rivière"},
            "creation_language": "en",
            "visibility": "public",
        }
        create_response = authenticated_client_alice.post(url_list, payload, format="json")
        point_type_id = create_response.data["id"]

        # Now get the point type
        url_detail = reverse("point-types:detail", args=[point_type_id])
        response = authenticated_client_alice.get(url_detail)

        assert response.status_code == status.HTTP_200_OK

        # Check schema
        assert "id" in response.data
        assert "type" in response.data
        assert "names" in response.data
        assert "creation_language" in response.data
        assert "owner" in response.data
        assert "visibility" in response.data

        # Check values
        assert response.data["id"] == point_type_id
        assert response.data["type"] == "custom"
        assert response.data["names"]["en"] == "River"
        assert response.data["names"]["fr"] == "Rivière"
        assert response.data["creation_language"] == "en"
        assert response.data["visibility"] == "public"

    def test_get_point_type_not_found(self, authenticated_client_alice):
        """Test that getting a non-existent point type returns 404."""
        url = reverse("point-types:detail", args=["00000000-0000-0000-0000-000000000000"])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_point_type_requires_authentication(self, api_client):
        """Test that getting a point type requires authentication."""
        url = reverse("point-types:detail", args=["00000000-0000-0000-0000-000000000000"])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
