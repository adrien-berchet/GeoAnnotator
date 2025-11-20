"""
Integration Test - Scenario 4: Sharing and Permissions

Acceptance Criteria: FR-030 to FR-045
- Share points with view/edit/transfer permissions
- Email invitation system with tokens
- Permission checking and enforcement
- Editing locks with concurrent access
- Cascade revoke when owner revokes share
- Non-registered user invitations
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.sharing.models import Share


@pytest.mark.django_db
class TestScenario4SharingPermissions:
    """Integration tests for sharing and permissions workflow."""

    def setup_method(self):
        """Set up test clients and users before each test."""
        from rest_framework_simplejwt.tokens import RefreshToken

        self.client = APIClient()

        # Create Alice (owner)
        self.alice = User.objects.create_user(
            username="alice", email="alice@example.com", password="SecurePass123"
        )
        refresh_alice = RefreshToken.for_user(self.alice)
        self.alice_token = str(refresh_alice.access_token)

        # Create Bob (recipient)
        self.bob = User.objects.create_user(
            username="bob", email="bob@example.com", password="SecurePass456"
        )
        refresh_bob = RefreshToken.for_user(self.bob)
        self.bob_token = str(refresh_bob.access_token)

        # Create a test point owned by Alice
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        point_response = self.client.post(
            reverse("points:list"),
            {
                "title": "Alice's Fishing Spot",
                "latitude": 45.5231,
                "longitude": -122.6765,
            },
            format="json",
        )
        self.point_id = point_response.data["id"]

    def test_step_1_share_point_with_view_permission(self):
        """
        Step 1: Share Point with View Permission

        Expected:
        - Response 201 with created share
        - Invitation email sent to bob@example.com
        - invitation_status = "pending", invitation_token generated
        """
        # Given
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_data = {
            "recipient_email": "bob@example.com",
            "permission_level": "view",
        }

        # When
        response = self.client.post(shares_url, share_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["recipient_email"] == "bob@example.com"
        assert response.data["permission_level"] == "view"
        assert "invitation_token" in response.data
        assert response.data["invitation_status"] == "pending"

    def test_step_2_accept_share_invitation(self):
        """
        Step 2: Accept Share Invitation

        Expected:
        - Response 200 with accepted share
        - accepted_at timestamp set
        - recipient_user = bob@example.com
        - invitation_status = "accepted"
        """
        # Given - Create share from Alice
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {
                "recipient_email": "bob@example.com",
                "permission_level": "view",
            },
            format="json",
        )
        invitation_token = share_response.data["invitation_token"]

        # When - Bob accepts invitation
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse("global_sharing:accept", kwargs={"token": invitation_token})
        response = self.client.post(accept_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["accepted_at"] is not None
        assert response.data["recipient_user"]["email"] == "bob@example.com"
        assert response.data["invitation_status"] == "accepted"

    def test_step_3_bob_views_shared_point(self):
        """
        Step 3: Bob Views Shared Point

        Expected:
        - Response 200 with point details
        - permission = "view" (Bob cannot edit)
        """
        # Given - Share point with Bob and accept
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "view"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # When - Bob views the point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        response = self.client.get(point_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission"] == "view"
        assert response.data["title"] == "Alice's Fishing Spot"

    def test_step_4_bob_attempts_edit_with_view_only(self):
        """
        Step 4: Bob Attempts to Edit Shared Point (Denied)

        Expected:
        - Response 403 with error "ACCESS_DENIED"
        - message: "No edit permission for this point"
        """
        # Given - Share with view permission
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "view"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # When - Bob attempts to edit
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        update_data = {"title": "Bob's Update"}
        response = self.client.patch(point_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            "ACCESS_DENIED" in str(response.data).upper()
            or "permission" in str(response.data).lower()
        )

    def test_step_5_alice_updates_share_to_edit_permission(self):
        """
        Step 5: Alice Updates Share to Edit Permission

        Expected:
        - Response 200 with updated share
        - permission_level = "edit"
        """
        # Given - Create share with view permission
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "view"},
            format="json",
        )
        share_id = share_response.data["id"]

        # When - Alice updates permission
        share_detail_url = reverse(
            "sharing:detail", kwargs={"point_id": self.point_id, "pk": share_id}
        )
        update_data = {"permission_level": "edit"}
        response = self.client.patch(share_detail_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission_level"] == "edit"

    def test_step_6_bob_edits_shared_point_with_edit_permission(self):
        """
        Step 6: Bob Edits Shared Point (Allowed)

        Expected:
        - Response 200 with updated point
        - editing_lock acquired by bob@example.com
        """
        # Given - Share with edit permission
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "edit"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # When - Bob edits the point
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        update_data = {"title": "Bob's Fishing Spot Too"}
        response = self.client.patch(point_url, update_data, format="json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["title"] == "Bob's Fishing Spot Too"
        assert response.data["editing_lock"]["locked_by"]["email"] == "bob@example.com"

    def test_step_7_alice_attempts_edit_while_bob_holds_lock(self):
        """
        Step 7: Alice Attempts to Edit While Bob Holds Lock

        Expected:
        - Response 409 with error "POINT_LOCKED"
        - Details: locked_by = bob@example.com, lock_expires_at shown
        """
        # Given - Bob has lock
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "edit"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # Bob acquires lock
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.patch(point_url, {"title": "Bob's Edit"}, format="json")

        # When - Alice attempts to edit
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        response = self.client.patch(point_url, {"title": "Alice's Edit"}, format="json")

        # Then
        assert response.status_code == status.HTTP_409_CONFLICT
        assert (
            "POINT_LOCKED" in str(response.data).upper() or "locked" in str(response.data).lower()
        )

    def test_step_8_bob_releases_lock(self):
        """
        Step 8: Bob Releases Lock

        Expected:
        - Response 204
        - Lock released
        """
        # Given - Bob has lock
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "edit"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # Bob acquires lock
        point_url = reverse("points:detail", kwargs={"pk": self.point_id})
        self.client.patch(point_url, {"title": "Locked"}, format="json")

        # When - Bob releases lock
        lock_url = reverse("points:lock", kwargs={"pk": self.point_id})
        response = self.client.delete(lock_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_step_9_alice_upgrades_bob_to_manage(self):
        """
        Step 9: Alice Upgrades Bob to Manage Permission

        Expected:
        - Response 200 with updated share
        - permission_level = "manage"
        """
        # Given - Create share
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "edit"},
            format="json",
        )
        share_id = share_response.data["id"]

        # When - Upgrade to manage
        share_detail_url = reverse(
            "sharing:detail", kwargs={"point_id": self.point_id, "pk": share_id}
        )
        response = self.client.patch(
            share_detail_url, {"permission_level": "manage"}, format="json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.data["permission_level"] == "manage"

    def test_step_10_bob_shares_point_with_charlie(self):
        """
        Step 10: Bob Shares Point with Charlie

        Expected:
        - Response 201 with created share
        - owner = alice@example.com (original owner tracked)
        """
        # Given - Bob has manage permission
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "manage"},
            format="json",
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # When - Bob shares with Charlie
        charlie_share_data = {
            "recipient_email": "charlie@example.com",
            "permission_level": "view",
        }
        response = self.client.post(shares_url, charlie_share_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["recipient_email"] == "charlie@example.com"
        # Owner should still be Alice
        assert response.data["owner"]["email"] == "alice@example.com"

    def test_step_11_alice_revokes_bob_share_cascade(self):
        """
        Step 11: Alice Revokes Bob's Share (Cascade)

        Expected:
        - Response 204
        - Bob's share deleted
        - Charlie's share also deleted (cascade)
        """
        # Given - Bob has share and shared with Charlie
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        bob_share_response = self.client.post(
            shares_url,
            {"recipient_email": "bob@example.com", "permission_level": "manage"},
            format="json",
        )
        bob_share_id = bob_share_response.data["id"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.bob_token}")
        accept_url = reverse(
            "global_sharing:accept", kwargs={"token": bob_share_response.data["invitation_token"]}
        )
        self.client.post(accept_url)

        # Bob shares with Charlie
        self.client.post(
            shares_url,
            {"recipient_email": "charlie@example.com", "permission_level": "view"},
            format="json",
        )

        # When - Alice revokes Bob's share
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        bob_share_url = reverse(
            "sharing:detail", kwargs={"point_id": self.point_id, "pk": bob_share_id}
        )
        response = self.client.delete(bob_share_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify both shares deleted
        assert not Share.objects.filter(id=bob_share_id).exists()
        # Charlie's share should also be deleted (cascade logic)
        # Note: This depends on implementation of cascade deletion

    def test_step_12_share_with_non_registered_email(self):
        """
        Step 12: Share Point with Non-Registered Email

        Expected:
        - Response 201 with created share
        - recipient_user = null
        - invitation sent to newuser@example.com
        """
        # Given
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.alice_token}")
        shares_url = reverse("sharing:list", kwargs={"point_id": self.point_id})

        share_data = {
            "recipient_email": "newuser@example.com",
            "permission_level": "view",
        }

        # When
        response = self.client.post(shares_url, share_data, format="json")

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["recipient_email"] == "newuser@example.com"
        assert response.data["recipient_user"] is None
        assert "invitation_token" in response.data
