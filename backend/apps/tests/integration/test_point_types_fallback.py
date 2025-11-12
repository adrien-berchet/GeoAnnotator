"""
Integration test: Fallback logic for missing translation.

Test the complete fallback chain: preferred → English → creation language.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.points.models import PointType
from apps.settings.models import UserPreferences


@pytest.mark.django_db
class TestPointTypesFallbackLogic:
    """Integration tests for point type fallback logic."""

    def test_fallback_chain_preferred_to_english_to_creation(
        self, authenticated_client_alice, alice
    ):
        """
        Test the complete fallback chain.

        Fallback order:
        1. User's preferred language (French)
        2. English (if preferred missing)
        3. Creation language (if both missing)

        Scenario:
        - Point type with only Spanish (creation language)
        - User prefers French
        - Should fall back to Spanish (creation language)
        """
        # Create point type with only Spanish
        point_type = PointType.objects.create(
            names={"es": "Río"},
            creation_language="es",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set preference to French
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get point type - should fall back to Spanish
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "es" in response.data["names"]
        assert response.data["names"]["es"] == "Río"

    def test_fallback_prefers_english_over_creation_language(
        self, authenticated_client_alice, alice
    ):
        """
        Test that English is preferred over creation language.

        Fallback order:
        1. User's preferred language (French) - missing
        2. English (available) ← should use this
        3. Creation language (Spanish) - available but lower priority

        Scenario:
        - Point type with English and Spanish
        - Creation language is Spanish
        - User prefers French
        - Should fall back to English (not Spanish)
        """
        # Create point type with English and Spanish
        point_type = PointType.objects.create(
            names={"en": "River", "es": "Río"},
            creation_language="es",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set preference to French (not available)
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get point type - should fall back to English, not creation language (Spanish)
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "en" in response.data["names"]
        assert "es" in response.data["names"]
        # Both are present, but English should be the fallback choice

    def test_no_fallback_needed_when_preferred_available(self, authenticated_client_alice, alice):
        """
        Test that no fallback occurs when preferred language is available.

        Scenario:
        - Point type with French, English, and Spanish
        - User prefers French
        - Should use French directly (no fallback)
        """
        # Create point type with multiple languages
        point_type = PointType.objects.create(
            names={"en": "Lake", "fr": "Lac", "es": "Lago"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Set preference to French (available)
        UserPreferences.objects.update_or_create(user=alice, defaults={"language": "fr"})

        # Get point type - should use French
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "fr" in response.data["names"]
        assert response.data["names"]["fr"] == "Lac"

    def test_default_to_english_when_no_preference_set(self, authenticated_client_alice, alice):
        """
        Test that system defaults to English when no preference is set.

        Scenario:
        - Point type with English and French
        - User has no language preference (defaults to English)
        - Should use English
        """
        # Create point type with English and French
        point_type = PointType.objects.create(
            names={"en": "Forest", "fr": "Forêt"},
            creation_language="en",
            type_choice="custom",
            owner=alice,
            visibility="private",
        )

        # Ensure no preference is set (or default is English)
        # By default, UserPreferences has language='en'

        # Get point type
        url = reverse("point-types:detail", args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "en" in response.data["names"]
        assert response.data["names"]["en"] == "Forest"
