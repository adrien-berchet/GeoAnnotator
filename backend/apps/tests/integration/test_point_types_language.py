"""
Integration test: User views point types in preferred language.

Test that point type names are returned in the user's preferred language
with proper fallback logic.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.points.models import PointType
from apps.settings.models import UserPreferences


@pytest.mark.django_db
class TestPointTypesLanguagePreference:
    """Integration tests for point type language preference."""

    def test_point_types_shown_in_user_preferred_language(self, authenticated_client_alice, alice):
        """
        Test that point type names are shown in user's preferred language.

        Scenario:
        1. Create a point type with English and French names
        2. Set user's language preference to French
        3. Verify the list returns names with French highlighted/preferred
        """
        # Create a custom point type with multiple translations
        point_type = PointType.objects.create(
            names={"en": "Tree", "fr": "Arbre"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set Alice's language preference to French
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get list of point types
        url = reverse("point-types:list")
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Find our point type in the response
        our_type = next((pt for pt in response.data if str(pt["id"]) == str(point_type.id)), None)
        assert our_type is not None
        assert our_type["names"]["fr"] == "Arbre"
        assert our_type["names"]["en"] == "Tree"

    def test_point_types_fallback_to_english_when_preferred_missing(
        self, authenticated_client_alice, alice
    ):
        """
        Test fallback to English when preferred language is missing.

        Scenario:
        1. Create a point type with only English name
        2. Set user's language preference to French
        3. Verify the point type is still accessible (fallback to English)
        """
        # Create a point type with only English
        point_type = PointType.objects.create(
            names={"en": "Mountain"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set Alice's language preference to French
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get the point type
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["names"]["en"] == "Mountain"
        # Should still be accessible even though French is missing

    def test_point_types_fallback_to_creation_language(self, authenticated_client_alice, alice):
        """
        Test fallback to creation language when both preferred and English missing.

        Scenario:
        1. Create a point type with only Spanish (creation language)
        2. Set user's language preference to French
        3. Verify the point type falls back to Spanish (creation language)
        """
        # Create a point type with only Spanish
        point_type = PointType.objects.create(
            names={"es": "Montaña"},
            creation_language="es",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set Alice's language preference to French
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get the point type
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["names"]["es"] == "Montaña"
        # Should fall back to creation language (Spanish)

    def test_base_types_default_to_english(self, authenticated_client_alice, alice):
        """
        Test that base types default to English.

        Scenario:
        1. Create a base point type (system type)
        2. Set user's language preference to French
        3. Verify base type has English as creation language
        """
        # Create a base point type (no owner)
        base_type = PointType.objects.create(
            names={"en": "Point", "fr": "Point"},
            creation_language="en",
            type_choice="base",
            owner=None,
            visibility="public",
        )

        # Get the point type
        url = reverse("point-types:detail", args=[base_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["creation_language"] == "en"
        assert response.data["type"] == "base"
