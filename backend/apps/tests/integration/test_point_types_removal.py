"""
Integration test: Prevent removal of last translation.

Test that at least one translation must remain.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.points.models import PointType


@pytest.mark.django_db
class TestPointTypesTranslationRemoval:
    """Integration tests for translation removal constraints."""

    def test_prevent_removal_of_last_translation(
        self, authenticated_client_alice, alice
    ):
        """
        Test that removing the last translation is prevented.

        Scenario:
        1. Create a point type with only one translation
        2. Try to remove it (set names to empty dict)
        3. Verify validation error (400)
        """
        # Create a point type with only English
        point_type = PointType.objects.create(
            names={"en": "Cliff"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private"
        )

        # Try to remove all translations
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {
            "names": {}
        }
        response = authenticated_client_alice.patch(
            url, update_payload, format="json"
        )

        # Should fail with 400
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_can_remove_one_translation_when_multiple_exist(
        self, authenticated_client_alice, alice
    ):
        """
        Test that removing one translation is OK when others remain.

        Scenario:
        1. Create a point type with English and French
        2. Remove French (keeping English)
        3. Verify success
        """
        # Create a point type with two translations
        point_type = PointType.objects.create(
            names={"en": "Beach", "fr": "Plage"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private"
        )

        # Remove French (keep English)
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {
            "names": {"en": "Beach"}
        }
        response = authenticated_client_alice.patch(
            url, update_payload, format="json"
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 1
        assert "en" in response.data["names"]
        assert "fr" not in response.data["names"]

    def test_can_replace_last_translation_with_different_language(
        self, authenticated_client_alice, alice
    ):
        """
        Test that replacing the last translation with a different language is OK.

        Scenario:
        1. Create a point type with only English
        2. Replace English with French (change creation language)
        3. Verify success (at least one translation remains)
        """
        # Create a point type with only English
        point_type = PointType.objects.create(
            names={"en": "Canyon"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private"
        )

        # Replace with French only
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {
            "names": {"fr": "Canyon"}
        }
        response = authenticated_client_alice.patch(
            url, update_payload, format="json"
        )

        # Should succeed (one translation still exists)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 1
        assert "fr" in response.data["names"]

    def test_can_remove_multiple_but_keep_at_least_one(
        self, authenticated_client_alice, alice
    ):
        """
        Test that removing multiple translations is OK if at least one remains.

        Scenario:
        1. Create a point type with English, French, Spanish, German
        2. Remove French and Spanish (keep English and German)
        3. Verify success
        """
        # Create a point type with four translations
        point_type = PointType.objects.create(
            names={
                "en": "Island",
                "fr": "Île",
                "es": "Isla",
                "de": "Insel"
            },
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private"
        )

        # Remove French and Spanish, keep English and German
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {
            "names": {
                "en": "Island",
                "de": "Insel"
            }
        }
        response = authenticated_client_alice.patch(
            url, update_payload, format="json"
        )

        # Should succeed
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 2
        assert "en" in response.data["names"]
        assert "de" in response.data["names"]
        assert "fr" not in response.data["names"]
        assert "es" not in response.data["names"]

    def test_validation_error_message_for_empty_names(
        self, authenticated_client_alice, alice
    ):
        """
        Test that a clear error message is returned when trying to remove all names.

        Scenario:
        1. Create a point type
        2. Try to remove all translations
        3. Verify error message is clear and helpful
        """
        # Create a point type
        point_type = PointType.objects.create(
            names={"en": "Desert"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private"
        )

        # Try to remove all translations
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {
            "names": {}
        }
        response = authenticated_client_alice.patch(
            url, update_payload, format="json"
        )

        # Should fail with clear error message
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "names" in response.data or "error" in response.data

    def test_creation_requires_at_least_one_translation(
        self, authenticated_client_alice
    ):
        """
        Test that creating a point type with no translations is prevented.

        Scenario:
        1. Try to create a point type with empty names
        2. Verify validation error
        """
        url = reverse("point-types:list")
        payload = {
            "names": {},
            "creation_language": "en",
            "visibility": "private"
        }
        response = authenticated_client_alice.post(url, payload, format="json")

        # Should fail
        assert response.status_code == status.HTTP_400_BAD_REQUEST
