"""
Contract test: Update a custom point type (add translation).

Test the PATCH /api/point-types/{id}/ endpoint contract.
"""

import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUpdatePointTypeContract:
    """Contract tests for updating point types."""

    def test_update_point_type_returns_200_with_object(
        self, authenticated_client_alice
    ):
        """
        Test that PATCH /api/point-types/{id}/ returns 200 with updated object.

        Contract:
        - Status: 200 OK
        - Body: Updated point type object
        - Request: names (map with added/modified translations)
        """
        # First create a point type
        url_list = reverse("point-types:list")
        payload = {
            "names": {"en": "Tree"},
            "creation_language": "en",
            "visibility": "private"
        }
        create_response = authenticated_client_alice.post(
            url_list, payload, format="json"
        )
        point_type_id = create_response.data["id"]

        # Now update it with a French translation
        url_detail = reverse("point-types:detail", args=[point_type_id])
        update_payload = {
            "names": {
                "en": "Tree",
                "fr": "Arbre"
            }
        }
        response = authenticated_client_alice.patch(
            url_detail, update_payload, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, dict)

    def test_update_point_type_response_schema(
        self, authenticated_client_alice
    ):
        """
        Test that updated point type has the correct schema.

        Contract:
        - id: unchanged
        - type: "custom"
        - names: object with both original and new translations
        - creation_language: unchanged
        - owner: unchanged
        - visibility: unchanged (unless explicitly updated)
        """
        # Create a point type
        url_list = reverse("point-types:list")
        payload = {
            "names": {"en": "Lake"},
            "creation_language": "en",
            "visibility": "public"
        }
        create_response = authenticated_client_alice.post(
            url_list, payload, format="json"
        )
        point_type_id = create_response.data["id"]
        original_owner = create_response.data["owner"]

        # Update with Spanish translation
        url_detail = reverse("point-types:detail", args=[point_type_id])
        update_payload = {
            "names": {
                "en": "Lake",
                "es": "Lago"
            }
        }
        response = authenticated_client_alice.patch(
            url_detail, update_payload, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Check that ID and other fields are unchanged
        assert response.data["id"] == point_type_id
        assert response.data["type"] == "custom"
        assert response.data["creation_language"] == "en"
        assert response.data["owner"] == original_owner
        assert response.data["visibility"] == "public"

        # Check that names include both translations
        assert response.data["names"]["en"] == "Lake"
        assert response.data["names"]["es"] == "Lago"

    def test_update_point_type_add_multiple_translations(
        self, authenticated_client_alice
    ):
        """Test adding multiple translations at once."""
        # Create a point type
        url_list = reverse("point-types:list")
        payload = {
            "names": {"en": "Hill"},
            "creation_language": "en",
            "visibility": "private"
        }
        create_response = authenticated_client_alice.post(
            url_list, payload, format="json"
        )
        point_type_id = create_response.data["id"]

        # Add multiple translations
        url_detail = reverse("point-types:detail", args=[point_type_id])
        update_payload = {
            "names": {
                "en": "Hill",
                "fr": "Colline",
                "es": "Colina",
                "de": "Hügel"
            }
        }
        response = authenticated_client_alice.patch(
            url_detail, update_payload, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 4
        assert response.data["names"]["fr"] == "Colline"
        assert response.data["names"]["es"] == "Colina"
        assert response.data["names"]["de"] == "Hügel"

    def test_update_point_type_requires_authentication(self, api_client):
        """Test that updating a point type requires authentication."""
        url = reverse("point-types:detail", args=["00000000-0000-0000-0000-000000000000"])
        payload = {
            "names": {"en": "Tree", "fr": "Arbre"}
        }
        response = api_client.patch(url, payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_point_type_cannot_remove_all_translations(
        self, authenticated_client_alice
    ):
        """Test that removing all translations is not allowed."""
        # Create a point type
        url_list = reverse("point-types:list")
        payload = {
            "names": {"en": "Park"},
            "creation_language": "en",
            "visibility": "private"
        }
        create_response = authenticated_client_alice.post(
            url_list, payload, format="json"
        )
        point_type_id = create_response.data["id"]

        # Try to update with empty names
        url_detail = reverse("point-types:detail", args=[point_type_id])
        update_payload = {
            "names": {}
        }
        response = authenticated_client_alice.patch(
            url_detail, update_payload, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
