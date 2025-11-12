"""
Integration Test - Scenario 7: Public Point Browsing

Acceptance Criteria: FR-063 to FR-068
- Create public points
- Browse public points (authenticated users)
- View public point details
- Permission checks (view-only for non-owners)
- Anonymous access (if implemented)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User


@pytest.mark.django_db
class TestScenario7PublicPointBrowsing:
    """Integration tests for public point browsing workflow."""

    def setup_method(self):
        """Set up test clients and users before each test."""
        self.client = APIClient()

        # Create and authenticate Alice (point owner)
        self.alice = User.objects.create_user(email="alice@example.com", password="SecurePass123")
        alice_login = self.client.post(
            reverse("authentication:login"),
            {"email": "alice@example.com", "password": "SecurePass123"},
            format="json",
        )
        self.alice_token = alice_login.data["access"]

        # Create and authenticate Bob (viewer)
        self.bob = User.objects.create_user(email="bob@example.com", password="SecurePass456")
        bob_login = self.client.post(
            reverse("authentication:login"),
            {"email": "bob@example.com", "password": "SecurePass456"},
            format="json",
        )
        self.bob_token = bob_login.data["access"]

        self.points_url = reverse("points:list")

    def test_step_1_alice_creates_public_point(self):
        """
        Step 1: Alice Creates Public Point

        Expected:
        - Response 201 with created point
        - is_public = true
        """
        # Given
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        point_data = {
            "title": "Public Trail",
            "latitude": 45.5000,
            "longitude": -122.7000,
            "is_public": True,
        }

        # When
        response = self.client.post(self.points_url, point_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_public"] is True
        assert response.data["title"] == "Public Trail"
        assert response.data["owner"]["email"] == "alice@example.com"

    def test_step_2_bob_browses_public_points(self):
        """
        Step 2: Bob Browses Public Points

        Expected:
        - Response 200 with public points
        - Includes Alice's public point, excludes her private points
        """
        # Given - Alice creates public and private points
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        public_response = self.client.post(
            self.points_url,
            {
                "title": "Alice's Public Point",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )
        public_point_id = public_response.data["id"]

        private_response = self.client.post(
            self.points_url,
            {
                "title": "Alice's Private Point",
                "latitude": 45.5100,
                "longitude": -122.7100,
                "is_public": False,
            },
            format="json",
        )
        private_point_id = private_response.data["id"]

        # When - Bob browses public points
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        response = self.client.get(self.points_url, {"visibility": "public"})

        # Then
        assert response.status_code == status.HTTP_200_OK

        point_ids = [p["id"] for p in response.data["results"]]
        point_titles = [p["title"] for p in response.data["results"]]

        # Should include public point
        assert public_point_id in point_ids
        assert "Alice's Public Point" in point_titles

        # Should NOT include private point
        assert private_point_id not in point_ids
        assert "Alice's Private Point" not in point_titles

    def test_step_3_bob_views_public_point_details(self):
        """
        Step 3: Bob Views Public Point Details

        Expected:
        - Response 200 with point details
        - permission = "view" (Bob cannot edit public points he doesn't own)
        """
        # Given - Alice creates a public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        create_response = self.client.post(
            self.points_url,
            {
                "title": "Public Viewpoint",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )
        public_point_id = create_response.data["id"]

        # When - Bob views the public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        point_url = reverse("points:detail", kwargs={"pk": public_point_id})
        response = self.client.get(point_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Public Viewpoint"
        assert response.data["permission"] == "view"
        assert response.data["owner"]["email"] == "alice@example.com"

    def test_step_4_bob_cannot_edit_public_point(self):
        """
        Step 4: Bob Cannot Edit Public Point

        Expected:
        - Response 403 with error "ACCESS_DENIED"
        """
        # Given - Alice creates a public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        create_response = self.client.post(
            self.points_url,
            {
                "title": "Public Point",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )
        public_point_id = create_response.data["id"]

        # When - Bob attempts to edit
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        point_url = reverse("points:detail", kwargs={"pk": public_point_id})
        update_data = {"title": "Bob's Update"}
        response = self.client.patch(point_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            "ACCESS_DENIED" in str(response.data).upper()
            or "permission" in str(response.data).lower()
        )

    def test_step_5_anonymous_user_browses_public_points(self):
        """
        Step 5: Anonymous User Browses Public Points (if implemented)

        Expected:
        - Response 200 with public points (if anonymous access enabled)
        - OR Response 401 (if authentication required)
        """
        # Given - Alice creates a public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_url,
            {
                "title": "Public for All",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )

        # When - Anonymous user (no credentials)
        self.client.credentials()  # Clear credentials
        response = self.client.get(self.points_url, {"visibility": "public"})

        # Then - Accept either 200 (anonymous access) or 401 (auth required)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

        if response.status_code == status.HTTP_200_OK:
            # Just verify the response structure is correct
            assert "results" in response.data

    def test_complete_public_browsing_flow(self):
        """
        Complete Flow: Create Public → Bob Views → Alice Makes Private → Bob Cannot View

        This test validates the public/private visibility workflow.
        """
        # Step 1: Alice creates public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        create_response = self.client.post(
            self.points_url,
            {
                "title": "Visibility Test Point",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )
        point_id = create_response.data["id"]
        point_url = reverse("points:detail", kwargs={"pk": point_id})

        # Step 2: Bob can view public point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        bob_view_response = self.client.get(point_url)
        assert bob_view_response.status_code == status.HTTP_200_OK

        # Step 3: Alice makes it private
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        update_response = self.client.patch(point_url, {"is_public": False}, format="json")
        assert update_response.status_code == status.HTTP_200_OK

        # Step 4: Bob can no longer view it
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        bob_view_private_response = self.client.get(point_url)
        assert bob_view_private_response.status_code == status.HTTP_404_NOT_FOUND

    def test_public_points_in_search_results(self):
        """
        Test that public points appear in search results for all users.

        Expected:
        - Bob can find Alice's public points via search
        - Bob cannot find Alice's private points via search
        """
        # Given - Alice creates public and private points with searchable text
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_url,
            {
                "title": "Public Garden Landmark",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )

        self.client.post(
            self.points_url,
            {
                "title": "Private Garden Secret",
                "latitude": 45.5100,
                "longitude": -122.7100,
                "is_public": False,
            },
            format="json",
        )

        # When - Bob searches for "garden"
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        search_response = self.client.get(self.points_url, {"search": "garden"})

        # Then
        assert search_response.status_code == status.HTTP_200_OK

        point_titles = [p["title"] for p in search_response.data["results"]]

        # Should find public garden
        assert "Public Garden Landmark" in point_titles

        # Should NOT find private garden
        assert "Private Garden Secret" not in point_titles

    def test_alice_can_see_own_private_and_public_points(self):
        """
        Test that point owner can see both their public and private points.

        Expected:
        - Alice can see all her points regardless of is_public flag
        """
        # Given - Alice creates public and private points
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_url,
            {
                "title": "Alice's Public",
                "latitude": 45.5000,
                "longitude": -122.7000,
                "is_public": True,
            },
            format="json",
        )

        self.client.post(
            self.points_url,
            {
                "title": "Alice's Private",
                "latitude": 45.5100,
                "longitude": -122.7100,
                "is_public": False,
            },
            format="json",
        )

        # When - Alice lists her owned points
        list_response = self.client.get(self.points_url, {"visibility": "owned"})

        # Then
        assert list_response.status_code == status.HTTP_200_OK
        assert list_response.data["count"] >= 2

        point_titles = [p["title"] for p in list_response.data["results"]]
        assert "Alice's Public" in point_titles
        assert "Alice's Private" in point_titles
