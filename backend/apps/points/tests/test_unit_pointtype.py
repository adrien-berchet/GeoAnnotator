"""
Unit tests for PointType model.

Tests the PointType model functionality including:
- Creation and basic fields
- Validation rules (unique name per user, max 1000 types)
- Default icon fallback
- Relationships with User and Point models
"""
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from apps.points.models import PointType
from apps.authentication.models import User


@pytest.mark.unit
@pytest.mark.django_db
class TestPointTypeModel:
    """Unit tests for PointType model."""

    def test_create_point_type_success(self, alice):
        """Test creating a point type successfully."""
        point_type = PointType.objects.create(
            names={"en": "Restaurant"},
            icon="/icons/restaurant.svg",
            order=1,
            owner=alice,
            status="active"
        )

        assert point_type.id is not None
        assert point_type.names == {"en": "Restaurant"}
        assert point_type.icon == "/icons/restaurant.svg"
        assert point_type.order == 1
        assert point_type.owner == alice
        assert point_type.status == "active"

    def test_create_point_type_with_default_icon(self, alice):
        """Test creating a point type without specifying icon uses default."""
        point_type = PointType.objects.create(
            names={"en": "Generic"},
            owner=alice,
            order=1
        )

        default_type = PointType.get_default_type()

        # Should use default icon
        assert point_type.icon is not None
        assert point_type.icon == default_type.icon

    def test_create_base_type_without_user(self):
        """Test creating a base type without user_id (system default)."""
        base_type = PointType.objects.create(
            names={"en": "Point"},
            icon="/icons/point.svg",
            order=0,
            owner=None,
            status="active"
        )

        assert base_type.owner is None
        assert base_type.names == {"en": "Point"}

    def test_unique_name_per_user(self, alice):
        """Test that type names must be unique per user."""
        PointType.objects.create(
            names={"en": "Café"},
            owner=alice,
            order=1
        )

        # Attempting to create another type with same name for same user should fail
        with pytest.raises((IntegrityError, ValidationError)):
            PointType.objects.create(
                names={"en": "Café"},
                owner=alice,
                order=2
            )

    def test_same_name_different_users_allowed(self, alice, bob):
        """Test that different users can have types with the same name."""
        type_alice = PointType.objects.create(
            names={"en": "Favorite"},
            owner=alice,
            order=1
        )

        type_bob = PointType.objects.create(
            names={"en": "Favorite"},
            owner=bob,
            order=1
        )

        assert type_alice.names == type_bob.names
        assert type_alice.owner != type_bob.owner

    @pytest.mark.skip(reason="Max types validation is tested in API contract tests")
    def test_max_types_per_user(self, alice):
        """Test that users cannot create more than 1000 types."""
        # This validation is enforced at the serializer/view level
        # and is covered by contract tests in test_contract_pointtypes.py
        # Unit testing this requires creating 1000 records which is slow
        pass

    def test_order_field(self, alice):
        """Test order field for sorting types."""
        type1 = PointType.objects.create(names={"en": "First"}, owner=alice, order=1)
        type2 = PointType.objects.create(names={"en": "Second"}, owner=alice, order=2)
        type3 = PointType.objects.create(names={"en": "Third"}, owner=alice, order=0)

        types = PointType.objects.filter(owner=alice).order_by('order')
        assert list(types) == [type3, type1, type2]

    def test_status_field(self, alice):
        """Test status field for soft delete."""
        point_type = PointType.objects.create(
            names={"en": "Test"},
            owner=alice,
            order=1,
            status="active"
        )

        # Mark as deleted
        point_type.status = "deleted"
        point_type.save()

        assert point_type.status == "deleted"

    def test_icon_reuse_allowed(self, alice):
        """Test that multiple types can use the same icon."""
        icon_path = "/icons/generic.svg"

        type1 = PointType.objects.create(names={"en": "Type1"}, owner=alice, order=1, icon=icon_path)
        type2 = PointType.objects.create(names={"en": "Type2"}, owner=alice, order=2, icon=icon_path)

        assert type1.icon == type2.icon
        assert type1.names != type2.names

    def test_str_representation(self, alice):
        """Test string representation of PointType."""
        point_type = PointType.objects.create(
            names={"en": "Restaurant"},
            owner=alice,
            order=1
        )

        assert "Restaurant" in str(point_type)

    @pytest.mark.django_db
    def test_cascade_delete_user(self, alice):
        """Test that deleting a user cascades to their types."""
        point_type = PointType.objects.create(
            names={"en": "Test"},
            owner=alice,
            order=1
        )

        point_type_id = point_type.id
        alice.delete()

        # Type should be cascade deleted since ForeignKey has on_delete=CASCADE
        assert not PointType.objects.filter(id=point_type_id).exists()
