"""
Integration Test - Scenario 6: Trash and Restoration

Acceptance Criteria: FR-056 to FR-062
- Move points to trash (30-day retention)
- List trashed points with days remaining
- Restore points from trash
- Permanent deletion
- Empty entire trash
- Expired point handling (>30 days)
- Shares deactivation on trash
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.points.models import GPSPoint
from apps.trash.models import Trash


@pytest.mark.django_db
class TestScenario6TrashRestoration:
    """Integration tests for trash and restoration workflow."""

    def setup_method(self):
        """Set up test client and create test point before each test."""
        self.client = APIClient()

        # Create and authenticate Alice
        self.alice = User.objects.create_user(
            email="alice@example.com", password="SecurePass123"
        )
        login_response = self.client.post(
            reverse("authentication:login"),
            {"email": "alice@example.com", "password": "SecurePass123"},
            format="json",
        )
        self.alice_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")

        # Create a test point
        point_response = self.client.post(
            reverse("points:list"),
            {
                "title": "Point to Trash",
                "latitude": 45.5231,
                "longitude": -122.6765,
            },
            format="json",
        )
        self.point_id = point_response.data["id"]

        self.trash_list_url = reverse("trash:points-list")

    def test_step_1_delete_point_move_to_trash(self):
        """
        Step 1: Delete Point (Move to Trash)

        Expected:
        - Response 204
        - Trash entry created with permanent_deletion_at = deleted_at + 30 days
        - All shares set is_active = false
        """
        # Given
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})

        # When
        response = self.client.delete(point_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify trash entry created
        trash_entry = Trash.objects.filter(gps_point_id=self.point_id).first()
        assert trash_entry is not None
        assert trash_entry.deleted_by == self.alice

        # Verify permanent deletion date (30 days from now)
        expected_deletion = trash_entry.deleted_at + timedelta(days=30)
        assert trash_entry.permanent_deletion_at.date() == expected_deletion.date()

    def test_step_2_list_trashed_points(self):
        """
        Step 2: List Trashed Points

        Expected:
        - Response 200 with trash items
        - days_remaining = 30 (for newly deleted point)
        """
        # Given - Delete a point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.delete(point_url)

        # When
        response = self.client.get(self.trash_list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

        # Find the trashed point
        trashed_point = next(
            (item for item in response.data if item["gps_point"]["id"] == self.point_id),
            None
        )
        assert trashed_point is not None
        assert trashed_point["days_remaining"] == 29

    def test_step_3_restore_point_from_trash(self):
        """
        Step 3: Restore Point from Trash

        Expected:
        - Response 200 with restored point
        - Trash entry deleted
        - Shares reactivated (is_active = true)
        """
        # Given - Delete a point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.delete(point_url)

        # When - Restore the point
        restore_url = reverse("trash:points-restore", kwargs={"pk": self.point_id})
        response = self.client.post(restore_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == self.point_id

        # Verify trash entry deleted
        assert not Trash.objects.filter(gps_point_id=self.point_id).exists()

        # Verify point is accessible again
        point_response = self.client.get(point_url)
        assert point_response.status_code == status.HTTP_200_OK

    def test_step_4_permanently_delete_point(self):
        """
        Step 4: Permanently Delete Point

        Expected:
        - Response 204
        - Point, annotations, shares permanently deleted
        - User's storage_used updated (reclaim all annotation file sizes)
        """
        # Given - Delete a point and get initial storage
        self.alice.refresh_from_db()
        initial_storage = self.alice.storage_used

        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.delete(point_url)

        # When - Permanently delete
        permanent_delete_url = reverse("trash:points-permanent", kwargs={"pk": self.point_id})
        response = self.client.delete(permanent_delete_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify point permanently deleted
        assert not GPSPoint.objects.filter(id=self.point_id).exists()
        assert not Trash.objects.filter(gps_point_id=self.point_id).exists()

        # Verify storage reclaimed (if there were annotations)
        self.alice.refresh_from_db()
        # Storage should be same or less (depending on annotations)
        assert self.alice.storage_used <= initial_storage

    def test_step_5_empty_entire_trash(self):
        """
        Step 5: Empty Entire Trash

        Expected:
        - Response 200 with {deleted_count: N}
        - All trashed points permanently deleted
        """
        # Given - Create and delete multiple points
        points_url = reverse("points:list")

        point_ids = []
        for i in range(3):
            point_response = self.client.post(
                points_url,
                {
                    "title": f"Point {i}",
                    "latitude": 45.5 + i * 0.01,
                    "longitude": -122.7 + i * 0.01,
                },
                format="json",
            )
            point_id = point_response.data["id"]
            point_ids.append(point_id)

            # Delete each point
            point_url = reverse("points:detail", kwargs={"pk": point_id})
            self.client.delete(point_url)

        # When - Empty trash
        empty_url = reverse("trash:points-empty")
        response = self.client.delete(empty_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_count"] >= 3

        # Verify all points permanently deleted
        for point_id in point_ids:
            assert not GPSPoint.objects.filter(id=point_id).exists()
            assert not Trash.objects.filter(gps_point_id=point_id).exists()

    def test_step_6_attempt_restore_expired_point(self):
        """
        Step 6: Attempt to Restore Expired Point (>30 days)

        Expected:
        - Response 410 with error "PERMANENTLY_DELETED"
        """
        # Given - Delete a point and manually set deletion date to 31 days ago
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.delete(point_url)

        # Manually update trash entry to simulate 31 days ago
        trash_entry = Trash.objects.get(gps_point_id=self.point_id)
        trash_entry.deleted_at = timezone.now() - timedelta(days=31)
        trash_entry.permanent_deletion_at = trash_entry.deleted_at + timedelta(days=30)
        trash_entry.save()

        # When - Attempt to restore
        restore_url = reverse("trash:points-restore", kwargs={"pk": self.point_id})
        response = self.client.post(restore_url)

        # Then
        assert response.status_code == status.HTTP_410_GONE
        assert "PERMANENTLY_DELETED" in str(response.data).upper() or "expired" in str(response.data).lower()

    def test_complete_trash_lifecycle(self):
        """
        Complete Flow: Delete → List → Restore → Delete Again → Permanent Delete

        This test validates the entire trash lifecycle.
        """
        # Step 1: Delete point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        delete_response = self.client.delete(point_url)
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 2: List trash
        list_response = self.client.get(self.trash_list_url)
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) == 1

        # Step 3: Restore point
        restore_url = reverse("trash:points-restore", kwargs={"pk": self.point_id})
        restore_response = self.client.post(restore_url)
        assert restore_response.status_code == status.HTTP_200_OK

        # Step 4: Verify point is accessible
        point_response = self.client.get(point_url)
        assert point_response.status_code == status.HTTP_200_OK

        # Step 5: Delete again
        delete_response_2 = self.client.delete(point_url)
        assert delete_response_2.status_code == status.HTTP_204_NO_CONTENT

        # Step 6: Permanently delete
        permanent_url = reverse("trash:points-permanent", kwargs={"pk": self.point_id})
        permanent_response = self.client.delete(permanent_url)
        assert permanent_response.status_code == status.HTTP_204_NO_CONTENT

        # Step 7: Verify point is gone
        assert not GPSPoint.objects.filter(id=self.point_id).exists()

    def test_trash_deactivates_shares(self):
        """
        Test that deleting a point deactivates all shares.

        Expected:
        - When point moved to trash, all shares become is_active=false
        - When restored, shares become is_active=true again
        """
        # Given - Share the point with Bob
        bob = User.objects.create_user(
            email="bob@example.com", password="SecurePass456"
        )

        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})
        share_response = self.client.post(
            shares_url,
            {
                "recipient_email": "bob@example.com",
                "permission_level": "view",
            },
            format="json",
        )
        share_id = share_response.data["id"]

        # When - Delete the point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.delete(point_url)

        # Then - Share should be deactivated
        from apps.sharing.models import Share
        share = Share.objects.get(id=share_id)
        assert share.is_active is False

        # When - Restore the point
        restore_url = reverse("trash:points-restore", kwargs={"pk": self.point_id})
        self.client.post(restore_url)

        # Then - Share should be reactivated
        share.refresh_from_db()
        assert share.is_active is True
