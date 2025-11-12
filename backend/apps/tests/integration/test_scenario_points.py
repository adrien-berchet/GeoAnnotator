"""
Integration Test - Scenario 2: GPS Point Creation and Management

Acceptance Criteria: FR-005 to FR-018
- Point CRUD operations (create, read, update, delete)
- Public/private visibility
- Tagging system
- Bounding box search
- Tag filtering
- Full-text search
- Editing lock acquisition
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.points.models import GPSPoint
from apps.points.models import Tag


@pytest.mark.django_db
class TestScenario2PointManagement:
    """Integration tests for GPS point creation and management workflow."""

    def setup_method(self):
        """Set up test client and authenticate user before each test."""
        self.client = APIClient()

        # Create and authenticate Alice
        self.alice = User.objects.create_user(email="alice@example.com", password="SecurePass123")
        login_response = self.client.post(
            reverse("authentication:login"),
            {"email": "alice@example.com", "password": "SecurePass123"},
            format="json",
        )
        self.alice_token = login_response.data["access"]

        # URLs
        self.points_list_url = reverse("points:list")

    def test_step_1_create_private_gps_point(self):
        """
        Step 1: Create Private GPS Point

        Expected:
        - Response 201 with created point
        - owner = alice@example.com
        - permission = "owner"
        - tags array contains 2 tags (auto-created if not exist)
        """
        # Given
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        point_data = {
            "title": "My Secret Fishing Spot",
            "description": "<p>Great trout fishing 🎣</p>",
            "latitude": 45.5231,
            "longitude": -122.6765,
            "tags": ["fishing", "river"],
            "is_public": False,
        }

        # When
        response = self.client.post(self.points_list_url, point_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["title"] == "My Secret Fishing Spot"
        assert response.data["owner"]["email"] == "alice@example.com"
        assert response.data["permission"] == "owner"
        assert len(response.data["tags"]) == 2
        assert response.data["is_public"] is False

        # Verify tags were created for alice
        assert Tag.objects.filter(name="fishing", owner=self.alice).exists()
        assert Tag.objects.filter(name="river", owner=self.alice).exists()

    def test_step_2_create_public_gps_point(self):
        """
        Step 2: Create Public GPS Point

        Expected:
        - Response 201 with created point
        - is_public = true
        """
        # Given
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        point_data = {
            "title": "Portland Japanese Garden",
            "description": "<p>Beautiful zen garden 🌸</p>",
            "latitude": 45.5195,
            "longitude": -122.7095,
            "tags": ["garden", "public"],
            "is_public": True,
        }

        # When
        response = self.client.post(self.points_list_url, point_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["is_public"] is True
        assert response.data["title"] == "Portland Japanese Garden"

    def test_step_3_list_alice_points(self):
        """
        Step 3: List Alice's Points

        Expected:
        - Response 200 with 2 points
        - Both owned by alice@example.com
        """
        # Given - Create 2 points
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_list_url,
            {
                "title": "Point 1",
                "latitude": 45.5231,
                "longitude": -122.6765,
                "is_public": False,
            },
            format="json",
        )

        self.client.post(
            self.points_list_url,
            {
                "title": "Point 2",
                "latitude": 45.5195,
                "longitude": -122.7095,
                "is_public": True,
            },
            format="json",
        )

        # When
        response = self.client.get(self.points_list_url, {"visibility": "owned"}, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2
        for point in response.data["results"]:
            assert point["owner"]["email"] == "alice@example.com"

    def test_step_4_search_points_by_bounding_box(self):
        """
        Step 4: Search Points by Bounding Box

        Expected:
        - Response 200 with points within bounding box
        - Only includes owned, shared, or public points
        """
        # Given - Create points inside and outside bbox
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        # Inside bbox
        self.client.post(
            self.points_list_url,
            {
                "title": "Inside BBox",
                "latitude": 45.5,
                "longitude": -122.7,
                "is_public": False,
            },
            format="json",
        )

        # Outside bbox
        self.client.post(
            self.points_list_url,
            {
                "title": "Outside BBox",
                "latitude": 46.0,
                "longitude": -123.0,
                "is_public": False,
            },
            format="json",
        )

        # When - Search with bounding box
        response = self.client.get(
            self.points_list_url,
            {"bbox": "-122.8,45.4,-122.6,45.6"},
            format="json",
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        # At least the inside point should be returned
        point_titles = [p["title"] for p in response.data["results"]]
        assert "Inside BBox" in point_titles

    def test_step_5_filter_points_by_tag(self):
        """
        Step 5: Filter Points by Tag

        Expected:
        - Response 200 with 1 point (My Secret Fishing Spot)
        """
        # Given - Create points with tags
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_list_url,
            {
                "title": "Fishing Spot",
                "latitude": 45.5231,
                "longitude": -122.6765,
                "tags": ["fishing"],
            },
            format="json",
        )

        self.client.post(
            self.points_list_url,
            {
                "title": "Hiking Trail",
                "latitude": 45.5195,
                "longitude": -122.7095,
                "tags": ["hiking"],
            },
            format="json",
        )

        # When - Use the correct endpoint for tag filtering
        search_tags_url = reverse("points:search-tags")
        response = self.client.post(search_tags_url, {"tags": ["fishing"]}, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["title"] == "Fishing Spot"

    def test_step_6_full_text_search(self):
        """
        Step 6: Full-Text Search

        Expected:
        - Response 200 with 1 point (Portland Japanese Garden)
        """
        # Given - Create points with searchable text
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        self.client.post(
            self.points_list_url,
            {
                "title": "Portland Japanese Garden",
                "description": "<p>Beautiful zen garden</p>",
                "latitude": 45.5195,
                "longitude": -122.7095,
            },
            format="json",
        )

        self.client.post(
            self.points_list_url,
            {
                "title": "Forest Trail",
                "description": "<p>Scenic hiking path</p>",
                "latitude": 45.5231,
                "longitude": -122.6765,
            },
            format="json",
        )

        # When - Use the correct endpoint for full-text search
        search_text_url = reverse("points:search-text")
        response = self.client.get(search_text_url, {"q": "garden"}, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert "Garden" in response.data[0]["title"]

    def test_step_7_update_gps_point(self):
        """
        Step 7: Update GPS Point

        Expected:
        - Response 200 with updated point
        - editing_lock acquired automatically
        - tags array now has 3 tags
        """
        # Given - Create a point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        create_response = self.client.post(
            self.points_list_url,
            {
                "title": "My Fishing Spot",
                "latitude": 45.5231,
                "longitude": -122.6765,
                "tags": ["fishing", "river"],
            },
            format="json",
        )
        point_id = create_response.data["id"]
        point_detail_url = reverse("points:detail", kwargs={"pk": point_id})

        # When - Update the point
        update_data = {
            "title": "My Updated Fishing Spot",
            "tags": ["fishing", "river", "trout"],
        }
        response = self.client.patch(point_detail_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "My Updated Fishing Spot"
        assert len(response.data["tags"]) == 3

        # Verify lock was acquired
        assert response.data["editing_lock"] is not None
        assert response.data["editing_lock"]["locked_by"]["email"] == "alice@example.com"

    def test_step_8_delete_gps_point_move_to_trash(self):
        """
        Step 8: Delete GPS Point (Move to Trash)

        Expected:
        - Response 204
        - Point moved to trash (30-day retention)
        """
        # Given - Create a point
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        create_response = self.client.post(
            self.points_list_url,
            {
                "title": "Point to Delete",
                "latitude": 45.5231,
                "longitude": -122.6765,
            },
            format="json",
        )
        point_id = create_response.data["id"]
        point_detail_url = reverse("points:detail", kwargs={"pk": point_id})

        # When - Delete the point
        response = self.client.delete(point_detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify point is in trash
        point = GPSPoint.objects.get(id=point_id)
        assert hasattr(point, "trash_entry")
        assert point.trash_entry is not None

    def test_complete_point_lifecycle(self):
        """
        Complete Flow: Create → List → Search → Update → Delete

        This test validates the entire point management lifecycle.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        # Step 1: Create private point
        create_response = self.client.post(
            self.points_list_url,
            {
                "title": "Complete Lifecycle Point",
                "description": "<p>Testing complete flow</p>",
                "latitude": 45.5231,
                "longitude": -122.6765,
                "tags": ["test", "lifecycle"],
                "is_public": False,
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        point_id = create_response.data["id"]

        # Step 2: List and verify point exists
        list_response = self.client.get(self.points_list_url)
        assert list_response.status_code == status.HTTP_200_OK
        point_ids = [p["id"] for p in list_response.data["results"]]
        assert point_id in point_ids

        # Step 3: Search by tag
        search_response = self.client.get(self.points_list_url, {"tags": "lifecycle"})
        assert search_response.status_code == status.HTTP_200_OK
        assert search_response.data["count"] >= 1

        # Step 4: Update point
        point_detail_url = reverse("points:detail", kwargs={"pk": point_id})
        update_response = self.client.patch(
            point_detail_url, {"title": "Updated Lifecycle Point"}, format="json"
        )
        assert update_response.status_code == status.HTTP_200_OK

        # Step 5: Delete point
        delete_response = self.client.delete(point_detail_url)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
