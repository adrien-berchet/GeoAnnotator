"""
Tests unitaires pour les vues DRF de points (GPSPoint, Tag, PointType).

Couvre CRUD, permissions, recherche spatiale, verrous et filtres.
"""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.points.models import GPSPoint
from apps.points.models import PointType
from apps.points.models import Tag
from apps.sharing.models import Share


@pytest.mark.django_db
class TestGPSPointCRUD:
    """Tests CRUD pour GPSPoint."""

    def test_list_accessible_points(
        self, authenticated_client_alice, gps_point_alice, public_gps_point_alice
    ):
        url = reverse("points:list")
        resp = authenticated_client_alice.get(url)
        assert resp.status_code == status.HTTP_200_OK
        # Alice voit ses deux points
        assert len(resp.data) >= 2

    def test_create_point_with_tags(self, authenticated_client_alice):
        url = reverse("points:list")
        data = {
            "title": "New Point",
            "latitude": 45.5,
            "longitude": -122.6,
            "tags": ["tag1", "tag2"],
            "is_public": False,
        }
        resp = authenticated_client_alice.post(url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["title"] == "New Point"
        point_id = resp.data["id"]
        p = GPSPoint.objects.get(id=point_id)
        assert {t.name for t in p.tags.all()} == {"tag1", "tag2"}

    def test_retrieve_own_point(self, authenticated_client_alice, gps_point_alice):
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_alice.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["id"] == str(gps_point_alice.id)

    def test_retrieve_not_found_returns_404(self, authenticated_client_alice):
        import uuid

        url = reverse("points:detail", args=[uuid.uuid4()])
        resp = authenticated_client_alice.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_private_point_of_other_returns_404(
        self, authenticated_client_bob, gps_point_alice
    ):
        # gps_point_alice est privé, Bob n'y a pas accès -> 404
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_bob.get(url)
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_update_own_point(self, authenticated_client_alice, gps_point_alice):
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_alice.patch(url, {"title": "Updated"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        gps_point_alice.refresh_from_db()
        assert gps_point_alice.title == "Updated"

    def test_update_shared_point_with_edit_permission(
        self, alice, bob, authenticated_client_bob, gps_point_alice
    ):
        # Bob reçoit edit
        Share.objects.create(
            gps_point=gps_point_alice,
            owner=alice,
            recipient_email="bob@example.com",
            recipient_user=bob,
            permission_level=Share.PERMISSION_EDIT,
            is_active=True,
        )
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_bob.patch(url, {"title": "Bob edited"}, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_update_without_permission_fails(self, authenticated_client_bob, gps_point_alice):
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_bob.patch(url, {"title": "Fail"}, format="json")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_own_point_moves_to_trash(self, authenticated_client_alice, gps_point_alice):
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_alice.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        gps_point_alice.refresh_from_db()
        assert hasattr(gps_point_alice, "trash_entry")

    def test_delete_non_owner_fails(self, authenticated_client_bob, gps_point_alice):
        url = reverse("points:detail", args=[gps_point_alice.id])
        resp = authenticated_client_bob.delete(url)
        assert resp.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestGPSPointSearch:
    """Tests recherche spatiale et par tags."""

    def test_search_bbox(self, authenticated_client_alice, gps_point_alice):
        # gps_point_alice = (-122.6765, 45.5231)
        url = reverse("points:search-bbox")
        data = {
            "min_longitude": -123.0,
            "min_latitude": 45.0,
            "max_longitude": -122.0,
            "max_latitude": 46.0,
        }
        resp = authenticated_client_alice.post(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 1

    def test_search_tags(self, authenticated_client_alice, gps_point_alice, tag_hiking):
        gps_point_alice.tags.add(tag_hiking)
        url = reverse("points:search-tags")
        data = {"tags": ["hiking"]}
        resp = authenticated_client_alice.post(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 1

    def test_search_text(self, authenticated_client_alice, gps_point_alice):
        url = reverse("points:search-text")
        resp = authenticated_client_alice.get(url, {"q": "Test Point"})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) >= 1


@pytest.mark.django_db
class TestGPSPointLock:
    """Tests verrous d'édition."""

    def test_acquire_lock(self, authenticated_client_alice, gps_point_alice):
        url = reverse("points:lock", args=[gps_point_alice.id])
        resp = authenticated_client_alice.post(url)
        assert resp.status_code == status.HTTP_200_OK
        assert "locked_by" in resp.data
        gps_point_alice.refresh_from_db()
        assert gps_point_alice.editing_lock_user is not None

    def test_release_lock(self, authenticated_client_alice, gps_point_alice):
        # Acquire first
        url_lock = reverse("points:lock", args=[gps_point_alice.id])
        authenticated_client_alice.post(url_lock)
        # Release
        resp = authenticated_client_alice.delete(url_lock)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        gps_point_alice.refresh_from_db()
        assert gps_point_alice.editing_lock_user is None


@pytest.mark.django_db
class TestTagViewSet:
    """Tests CRUD pour Tag."""

    def test_list_user_tags(self, authenticated_client_alice, tag_hiking, tag_fishing):
        url = reverse("tags:list")
        resp = authenticated_client_alice.get(url)
        assert resp.status_code == status.HTTP_200_OK
        names = [t["name"] for t in resp.data]
        assert "hiking" in names
        assert "fishing" in names

    def test_create_tag(self, authenticated_client_alice, alice):
        url = reverse("tags:list")
        resp = authenticated_client_alice.post(url, {"name": "camping"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert Tag.objects.filter(name="camping", owner=alice).exists()

    def test_create_duplicate_tag_fails(self, authenticated_client_alice, tag_hiking):
        url = reverse("tags:list")
        resp = authenticated_client_alice.post(url, {"name": "hiking"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_delete_tag(self, authenticated_client_alice, tag_hiking):
        url = reverse("tags:detail", args=[tag_hiking.id])
        resp = authenticated_client_alice.delete(url)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Tag.objects.filter(id=tag_hiking.id).exists()


@pytest.mark.django_db
class TestPointTypeViewSet:
    """Tests CRUD et reorder pour PointType."""

    def test_list_point_types(self, authenticated_client_alice):
        # Force création du type par défaut
        PointType.get_default_type()
        url = reverse("point-types:list")
        resp = authenticated_client_alice.get(url)
        assert resp.status_code == status.HTTP_200_OK
        # Au moins le type par défaut
        assert len(resp.data) >= 1

    def test_create_point_type(self, authenticated_client_alice, alice):
        url = reverse("point-types:list")
        data = {"names": {"en": "Cabin"}, "creation_language": "en", "icon": "🏠"}
        resp = authenticated_client_alice.post(url, data, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert PointType.objects.filter(names={"en": "Cabin"}, owner=alice).exists()

    def test_reorder_point_types(self, alice, authenticated_client_alice):
        base = PointType.get_default_type()
        mine = PointType.objects.create(
            names={"en": "Custom"}, creation_language="en", owner=alice, type_choice="custom"
        )
        url = reverse("point-types:reorder")
        data = {
            "order": [
                {"id": str(mine.id), "order": "1"},
                {"id": str(base.id), "order": "2"},
            ]
        }
        resp = authenticated_client_alice.post(url, data, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["success"] is True
