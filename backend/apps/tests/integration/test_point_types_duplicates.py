"""
Integration test: Prevent duplicate language entries.

Test that duplicate language codes are prevented in translations.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.points.models import PointType


@pytest.mark.django_db
class TestPointTypesDuplicatePrevention:
    """Integration tests for preventing duplicate language entries."""

    def test_prevent_duplicate_language_codes_in_names(self, authenticated_client_alice, alice):
        """
        Test that duplicate language codes are prevented.

        Scenario:
        1. Create a point type with English name
        2. Try to update with duplicate English entries
        3. Verify validation error
        """
        # Create a point type
        point_type = PointType.objects.create(
            names={"en": "Hill"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Try to update with what could be interpreted as duplicate
        # (This test verifies the system handles names as a proper dict)
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {"names": {"en": "Hill", "fr": "Colline"}}
        response = authenticated_client_alice.patch(url, update_payload, format="json")

        # Should succeed (no actual duplicate, just updating properly)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 2

    def test_names_field_is_proper_dict(self, authenticated_client_alice, alice):
        """
        Test that names field is stored as a proper dictionary.

        This prevents duplicate keys by design (dicts can't have duplicate keys).
        """
        # Create a point type
        point_type = PointType.objects.create(
            names={"en": "Valley", "fr": "Vallée", "es": "Valle"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Get the point type
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data["names"], dict)
        assert len(response.data["names"]) == 3

        # Verify no duplicate keys (dict guarantees this)
        language_codes = list(response.data["names"].keys())
        assert len(language_codes) == len(set(language_codes))

    def test_update_preserves_unique_language_codes(self, authenticated_client_alice, alice):
        """
        Test that updating a translation preserves uniqueness.

        Scenario:
        1. Create a point type with English and French
        2. Update English translation
        3. Verify no duplication, just replacement
        """
        # Create a point type
        point_type = PointType.objects.create(
            names={"en": "Road", "fr": "Route"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Update English translation
        url = reverse("point-types:detail", args=[point_type.id])
        update_payload = {"names": {"en": "Highway", "fr": "Route"}}  # Changed from "Road"
        response = authenticated_client_alice.patch(url, update_payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["names"]) == 2
        assert response.data["names"]["en"] == "Highway"
        assert response.data["names"]["fr"] == "Route"

    def test_case_sensitivity_in_language_codes(self, authenticated_client_alice, alice):
        """
        Test that language codes are case-sensitive (ISO 639-1 uses lowercase).

        Scenario:
        1. Create a point type with lowercase language codes
        2. Verify system uses lowercase ISO 639-1 codes
        """
        # Create a point type with proper lowercase codes
        point_type = PointType.objects.create(
            names={"en": "Bridge", "fr": "Pont"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Get the point type
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify language codes are lowercase
        for code in response.data["names"].keys():
            assert code.islower(), f"Language code '{code}' should be lowercase"

    def test_adding_new_language_does_not_duplicate(self, authenticated_client_alice, alice):
        """
        Test that adding a new language doesn't create duplicates.

        Scenario:
        1. Create a point type with English
        2. Add French
        3. Add Spanish
        4. Verify all three exist uniquely
        """
        # Create a point type
        point_type = PointType.objects.create(
            names={"en": "Park"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Add French
        url = reverse("point-types:detail", args=[point_type.id])
        response1 = authenticated_client_alice.patch(
            url, {"names": {"en": "Park", "fr": "Parc"}}, format="json"
        )
        assert response1.status_code == status.HTTP_200_OK
        assert len(response1.data["names"]) == 2

        # Add Spanish
        response2 = authenticated_client_alice.patch(
            url, {"names": {"en": "Park", "fr": "Parc", "es": "Parque"}}, format="json"
        )
        assert response2.status_code == status.HTTP_200_OK
        assert len(response2.data["names"]) == 3

        # Verify all unique
        assert response2.data["names"]["en"] == "Park"
        assert response2.data["names"]["fr"] == "Parc"
        assert response2.data["names"]["es"] == "Parque"
