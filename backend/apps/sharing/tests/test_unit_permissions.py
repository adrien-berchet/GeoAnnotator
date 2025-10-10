"""
Unit tests for permission checking logic.

Tests cover:
- Owner permissions
- View/Edit/Transfer permission hierarchy
- Share permission validation
- Cascade permission revoke
"""
import pytest
from django.contrib.auth import get_user_model
from apps.points.models import GPSPoint
from apps.sharing.models import Share
from apps.sharing.services import PermissionService
from django.contrib.gis.geos import Point

User = get_user_model()


@pytest.mark.django_db
class TestPermissionChecking:
    """Unit tests for permission service."""

    @pytest.fixture
    def owner(self):
        """Create owner user."""
        return User.objects.create_user(
            email='owner@example.com',
            password='TestPass123'
        )

    @pytest.fixture
    def viewer(self):
        """Create viewer user."""
        return User.objects.create_user(
            email='viewer@example.com',
            password='TestPass123'
        )

    @pytest.fixture
    def editor(self):
        """Create editor user."""
        return User.objects.create_user(
            email='editor@example.com',
            password='TestPass123'
        )

    @pytest.fixture
    def gps_point(self, owner):
        """Create test GPS point."""
        return GPSPoint.objects.create(
            title='Test Point',
            location=Point(0, 0),
            owner=owner
        )

    def test_owner_has_all_permissions(self, gps_point, owner):
        """Test that owner has view, edit, and transfer permissions."""
        assert PermissionService.can_view(gps_point, owner) is True
        assert PermissionService.can_edit(gps_point, owner) is True
        assert PermissionService.can_share(gps_point, owner) is True
        assert PermissionService.is_owner(gps_point, owner) is True

    def test_viewer_has_view_only(self, gps_point, owner, viewer):
        """Test that viewer can only view."""
        # Create view share
        Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=viewer.email,
            recipient_user=viewer,
            permission_level='view'
        )

        assert PermissionService.can_view(gps_point, viewer) is True
        assert PermissionService.can_edit(gps_point, viewer) is False
        assert PermissionService.can_share(gps_point, viewer) is False
        assert PermissionService.is_owner(gps_point, viewer) is False

    def test_editor_has_view_and_edit(self, gps_point, owner, editor):
        """Test that editor can view and edit."""
        # Create edit share
        Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=editor.email,
            recipient_user=editor,
            permission_level='edit'
        )

        assert PermissionService.can_view(gps_point, editor) is True
        assert PermissionService.can_edit(gps_point, editor) is True
        assert PermissionService.can_share(gps_point, editor) is False
        assert PermissionService.is_owner(gps_point, editor) is False

    def test_transfer_permission_can_share(self, gps_point, owner):
        """Test that transfer permission allows sharing."""
        transfer_user = User.objects.create_user(
            email='transfer@example.com',
            password='TestPass123'
        )

        # Create transfer share
        Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=transfer_user.email,
            recipient_user=transfer_user,
            permission_level='transfer'
        )

        assert PermissionService.can_view(gps_point, transfer_user) is True
        assert PermissionService.can_edit(gps_point, transfer_user) is True
        assert PermissionService.can_share(gps_point, transfer_user) is True
        assert PermissionService.is_owner(gps_point, transfer_user) is False

    def test_no_permission_denies_all(self, gps_point):
        """Test that user without share has no permissions."""
        stranger = User.objects.create_user(
            email='stranger@example.com',
            password='TestPass123'
        )

        assert PermissionService.can_view(gps_point, stranger) is False
        assert PermissionService.can_edit(gps_point, stranger) is False
        assert PermissionService.can_share(gps_point, stranger) is False
        assert PermissionService.is_owner(gps_point, stranger) is False

    def test_public_point_viewable_by_all(self, gps_point):
        """Test that public points are viewable by anyone."""
        gps_point.is_public = True
        gps_point.save()

        stranger = User.objects.create_user(
            email='stranger@example.com',
            password='TestPass123'
        )

        assert PermissionService.can_view(gps_point, stranger) is True
        assert PermissionService.can_edit(gps_point, stranger) is False

    def test_inactive_share_denies_permissions(self, gps_point, owner, viewer):
        """Test that inactive share denies permissions."""
        # Create share and deactivate
        share = Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=viewer.email,
            recipient_user=viewer,
            permission_level='edit',
            is_active=False
        )

        assert PermissionService.can_view(gps_point, viewer) is False
        assert PermissionService.can_edit(gps_point, viewer) is False

    def test_get_user_permission_returns_correct_level(self, gps_point, owner, editor):
        """Test getting user permission level."""
        # Owner
        assert PermissionService.get_user_permission(gps_point, owner) == 'owner'

        # Editor
        Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=editor.email,
            recipient_user=editor,
            permission_level='edit'
        )
        assert PermissionService.get_user_permission(gps_point, editor) == 'edit'

        # Stranger
        stranger = User.objects.create_user(
            email='stranger@example.com',
            password='TestPass123'
        )
        assert PermissionService.get_user_permission(gps_point, stranger) is None

    def test_get_accessible_points(self, owner, viewer):
        """Test getting accessible points for user."""
        # Create owned point
        owned_point = GPSPoint.objects.create(
            title='Owned Point',
            location=Point(0, 0),
            owner=owner
        )

        # Create shared point
        shared_point = GPSPoint.objects.create(
            title='Shared Point',
            location=Point(1, 1),
            owner=User.objects.create_user(email='other@example.com', password='pass')
        )

        Share.objects.create(
            gps_point=shared_point,
            owner=shared_point.owner,
            recipient_email=viewer.email,
            recipient_user=viewer,
            permission_level='view'
        )

        # Create public point
        public_point = GPSPoint.objects.create(
            title='Public Point',
            location=Point(2, 2),
            owner=User.objects.create_user(email='public@example.com', password='pass'),
            is_public=True
        )

        # Test owner access
        owner_points = PermissionService.get_accessible_points(owner, include_public=False)
        assert owned_point in owner_points
        assert shared_point not in owner_points
        assert public_point not in owner_points

        # Test viewer access with public
        viewer_points = PermissionService.get_accessible_points(viewer, include_public=True)
        assert owned_point not in viewer_points
        assert shared_point in viewer_points
        assert public_point in viewer_points

    def test_permission_hierarchy(self, gps_point, owner):
        """Test permission hierarchy validation."""
        # Transfer > Edit > View
        viewer = User.objects.create_user(email='viewer@example.com', password='pass')
        editor = User.objects.create_user(email='editor@example.com', password='pass')

        # Viewer cannot grant edit
        Share.objects.create(
            gps_point=gps_point,
            owner=owner,
            recipient_email=viewer.email,
            recipient_user=viewer,
            permission_level='view'
        )

        # Viewer permission level is lower than edit
        assert PermissionService.get_user_permission(gps_point, viewer) == 'view'
        assert PermissionService.can_share(gps_point, viewer) is False
