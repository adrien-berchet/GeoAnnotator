"""
Contract test: List all point types.

Test the GET /api/point-types/ endpoint contract.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestListPointTypesContract:
    """Contract tests for listing point types."""

    def test_list_point_types_returns_200_with_array(self, authenticated_client_alice):
        """
        Test that GET /api/point-types/ returns 200 with an array.

        Contract:
        - Status: 200 OK
        - Body: Array of point types
        - Each type has: id, type, names, creation_language, owner, visibility
        """
        url = reverse("point-types:list")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_list_point_types_response_schema(self, authenticated_client_alice):
        """
        Test that each point type in the list has the correct schema.

        Contract:
        - id: string (UUID)
        - type: string (enum: base, custom)
        - names: object (map of language_code: name)
        - creation_language: string (ISO 639-1 code)
        - owner: string or null
        - visibility: string (enum: public, private)
        """
        url = reverse("point-types:list")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK

        # If there are any point types, check the schema
        if len(response.data) > 0:
            point_type = response.data[0]

            # Check required fields exist
            assert "id" in point_type
            assert "type" in point_type
            assert "names" in point_type
            assert "creation_language" in point_type
            assert "owner" in point_type
            assert "visibility" in point_type

            # Check field types
            assert isinstance(point_type["id"], str)
            assert isinstance(point_type["type"], str)
            assert point_type["type"] in ["base", "custom"]
            assert isinstance(point_type["names"], dict)
            assert isinstance(point_type["creation_language"], str)
            assert point_type["owner"] is None or isinstance(point_type["owner"], str)
            assert isinstance(point_type["visibility"], str)
            assert point_type["visibility"] in ["public", "private"]

    def test_list_point_types_requires_authentication(self, api_client):
        """Test that the endpoint requires authentication."""
        url = reverse("point-types:list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
