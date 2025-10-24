"""
Contract tests for PointType Management API.

These tests validate the API contract for point type management.
They MUST FAIL until the views/endpoints are implemented (TDD approach).

Tests cover:
- POST /api/v1/types/ - Create point type
- GET /api/v1/types/ - List user's point types
- GET /api/v1/types/{id}/ - Get point type detail
- PATCH /api/v1/types/{id}/ - Update point type
- DELETE /api/v1/types/{id}/ - Delete point type
- PATCH /api/v1/types/reorder/ - Reorder point types
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.contract
@pytest.mark.critical
class TestPointTypeContract:
    """Contract tests for PointType Management API endpoints."""

    # POST /api/v1/types/ - Create point type
    def test_create_type_success(self, authenticated_client_alice):
        """Test successful point type creation."""
        url = reverse('point-types:list')
        data = {
            'name': 'Restaurant',
            'icon': '/icons/restaurant.svg',
            'order': 1
        }

        response = authenticated_client_alice.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['name'] == 'Restaurant'
        assert response.data['icon'] == '/icons/restaurant.svg'
        assert response.data['order'] == 1
        assert response.data['status'] == 'active'
        assert 'user' in response.data

    def test_create_type_without_icon_uses_default(self, authenticated_client_alice):
        """Test creating type without icon uses default."""
        url = reverse('point-types:list')
        data = {
            'name': 'Generic',
            'order': 1
        }

        response = authenticated_client_alice.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['icon'] is not None
        assert 'default' in response.data['icon'].lower() or 'point' in response.data['icon'].lower()

    def test_create_type_duplicate_name_same_user(self, authenticated_client_alice):
        """Test creating type with duplicate name for same user fails."""
        url = reverse('point-types:list')
        data = {'name': 'Café', 'order': 1}

        # First creation
        authenticated_client_alice.post(url, data, format='json')

        # Duplicate creation
        response = authenticated_client_alice.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'name' in str(response.data).lower() or 'unique' in str(response.data).lower()

    def test_create_type_exceeds_1000_limit(self, authenticated_client_alice):
        """Test that creating >1000 types fails."""
        # Note: In real tests, we'd need to create 1000 types first
        # For now, we'll test the validation logic exists

        url = reverse('point-types:list')

        # Create 1000 types
        for i in range(1000):
            data = {'name': f'Type_{i}', 'order': i}
            authenticated_client_alice.post(url, data, format='json')

        # Try to create 1001st type
        data = {'name': 'Type_1001', 'order': 1000}
        response = authenticated_client_alice.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'limit' in str(response.data).lower() or '1000' in str(response.data)

    def test_create_type_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot create types."""
        url = reverse('point-types:list')
        data = {'name': 'Test', 'order': 1}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # GET /api/v1/types/ - List point types
    def test_list_types_success(self, authenticated_client_alice, alice):
        """Test listing user's point types."""
        from apps.points.models import PointType

        # Create some types for Alice
        PointType.objects.create(names={'en': 'Type1'}, owner=alice, order=1)
        PointType.objects.create(names={'en': 'Type2'}, owner=alice, order=2)

        url = reverse('point-types:list')
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) >= 2

        # Check ordering
        assert response.data[0]['order'] <= response.data[1]['order']

    def test_list_types_only_own_types(self, authenticated_client_alice, authenticated_client_bob, alice, bob):
        """Test that users only see their own types."""
        from apps.points.models import PointType

        PointType.objects.create(names={'en': 'AliceType'}, owner=alice, order=1)
        PointType.objects.create(names={'en': 'BobType'}, owner=bob, order=1)

        url = reverse('point-types:list')

        # Alice should only see her types
        response_alice = authenticated_client_alice.get(url)
        assert response.status_code == status.HTTP_200_OK
        alice_type_names = [t['name'] for t in response_alice.data]
        assert 'AliceType' in alice_type_names
        assert 'BobType' not in alice_type_names

        # Bob should only see his types
        response_bob = authenticated_client_bob.get(url)
        bob_type_names = [t['name'] for t in response_bob.data]
        assert 'BobType' in bob_type_names
        assert 'AliceType' not in bob_type_names

    def test_list_types_includes_base_types(self, authenticated_client_alice):
        """Test that listing includes base types (user=None)."""
        from apps.points.models import PointType

        # Create base type
        PointType.objects.create(names={'en': 'Point'}, user=None, order=0)

        url = reverse('point-types:list')
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        type_names = [t['name'] for t in response.data]
        assert 'Point' in type_names

    def test_list_types_excludes_deleted(self, authenticated_client_alice, alice):
        """Test that listing excludes deleted types."""
        from apps.points.models import PointType

        active_type = PointType.objects.create(names={'en': 'Active'}, owner=alice, order=1)
        deleted_type = PointType.objects.create(names={'en': 'Deleted'}, owner=alice, order=2, status='deleted')

        url = reverse('point-types:list')
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        type_names = [t['name'] for t in response.data]
        assert 'Active' in type_names
        assert 'Deleted' not in type_names

    # GET /api/v1/types/{id}/ - Get point type detail
    def test_get_type_detail_success(self, authenticated_client_alice, alice):
        """Test getting point type detail."""
        from apps.points.models import PointType

        point_type = PointType.objects.create(
            names={'en': 'Museum'},
            icon='/icons/museum.svg',
            owner=alice,
            order=1
        )

        url = reverse('point-types:detail', args=[point_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(point_type.id)
        assert response.data['name'] == 'Museum'
        assert response.data['icon'] == '/icons/museum.svg'

    def test_get_type_detail_not_own_type(self, authenticated_client_alice, bob):
        """Test that user cannot get detail of another user's type."""
        from apps.points.models import PointType

        bob_type = PointType.objects.create(names={'en': 'BobType'}, owner=bob, order=1)

        url = reverse('point-types:detail', args=[bob_type.id])
        response = authenticated_client_alice.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # PATCH /api/v1/types/{id}/ - Update point type
    def test_update_type_success(self, authenticated_client_alice, alice):
        """Test successful point type update."""
        from apps.points.models import PointType

        point_type = PointType.objects.create(
            names={'en': 'Restaurant'},
            icon='/icons/restaurant.svg',
            owner=alice,
            order=1
        )

        url = reverse('point-types:detail', args=[point_type.id])
        data = {
            'name': 'Café',
            'icon': '/icons/cafe.svg'
        }

        response = authenticated_client_alice.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Café'
        assert response.data['icon'] == '/icons/cafe.svg'

    def test_update_type_duplicate_name(self, authenticated_client_alice, alice):
        """Test that updating to duplicate name fails."""
        from apps.points.models import PointType

        type1 = PointType.objects.create(names={'en': 'Type1'}, owner=alice, order=1)
        type2 = PointType.objects.create(names={'en': 'Type2'}, owner=alice, order=2)

        url = reverse('point-types:detail', args=[type2.id])
        data = {'name': 'Type1'}

        response = authenticated_client_alice.patch(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_type_not_own_type(self, authenticated_client_alice, bob):
        """Test that user cannot update another user's type."""
        from apps.points.models import PointType

        bob_type = PointType.objects.create(names={'en': 'BobType'}, owner=bob, order=1)

        url = reverse('point-types:detail', args=[bob_type.id])
        data = {'name': 'NewName'}

        response = authenticated_client_alice.patch(url, data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # DELETE /api/v1/types/{id}/ - Delete point type
    def test_delete_type_success(self, authenticated_client_alice, alice):
        """Test successful point type deletion (soft delete)."""
        from apps.points.models import PointType

        point_type = PointType.objects.create(names={'en': 'ToDelete'}, owner=alice, order=1)

        url = reverse('point-types:detail', args=[point_type.id])
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Type should still exist but marked as deleted
        point_type.refresh_from_db()
        assert point_type.status == 'deleted'

    def test_delete_type_switches_points_to_default(self, authenticated_client_alice, alice):
        """Test that deleting type switches associated points to default."""
        from apps.points.models import PointType, GPSPoint
        from django.contrib.gis.geos import Point

        # Create default type
        default_type = PointType.objects.create(names={'en': 'Point'}, user=None, order=0)

        # Create custom type
        custom_type = PointType.objects.create(names={'en': 'Custom'}, owner=alice, order=1)

        # Create point with custom type
        point = GPSPoint.objects.create(
            title='Test Point',
            location=Point(2.3522, 48.8566),
            owner=alice,
            type=custom_type
        )

        # Delete custom type
        url = reverse('point-types:detail', args=[custom_type.id])
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Point should now have default type
        point.refresh_from_db()
        assert point.type == default_type

    def test_delete_type_not_own_type(self, authenticated_client_alice, bob):
        """Test that user cannot delete another user's type."""
        from apps.points.models import PointType

        bob_type = PointType.objects.create(names={'en': 'BobType'}, owner=bob, order=1)

        url = reverse('point-types:detail', args=[bob_type.id])
        response = authenticated_client_alice.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # PATCH /api/v1/types/reorder/ - Reorder point types
    def test_reorder_types_success(self, authenticated_client_alice, alice):
        """Test successful type reordering."""
        from apps.points.models import PointType

        type1 = PointType.objects.create(names={'en': 'Type1'}, owner=alice, order=1)
        type2 = PointType.objects.create(names={'en': 'Type2'}, owner=alice, order=2)
        type3 = PointType.objects.create(names={'en': 'Type3'}, owner=alice, order=3)

        url = reverse('pointtype-reorder')
        data = {
            'order': [
                {'id': str(type3.id), 'order': 1},
                {'id': str(type1.id), 'order': 2},
                {'id': str(type2.id), 'order': 3},
            ]
        }

        response = authenticated_client_alice.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        # Verify new order
        type1.refresh_from_db()
        type2.refresh_from_db()
        type3.refresh_from_db()

        assert type3.order == 1
        assert type1.order == 2
        assert type2.order == 3
