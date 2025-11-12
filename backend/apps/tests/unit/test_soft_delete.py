"""
Unit test: Soft delete behavior

Test the soft delete functionality for User model.
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.authentication.models import User


@pytest.mark.django_db
class TestSoftDelete:
    """Unit tests for soft delete behavior."""

    def test_active_user_has_null_deleted_at(self, user_alice):
        """Test that active users have deleted_at=None."""
        assert user_alice.deleted_at is None

    def test_setting_deleted_at_marks_user_deleted(self, user_alice):
        """Test that setting deleted_at marks user as deleted."""
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        assert user_alice.deleted_at is not None

    def test_deleted_users_excluded_from_active_manager(self, user_alice):
        """Test that deleted users are excluded from User.active queryset."""
        user_id = user_alice.id

        # Initially in active manager
        assert User.active.filter(id=user_id).exists()

        # Soft delete
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # No longer in active manager
        assert not User.active.filter(id=user_id).exists()

    def test_deleted_users_accessible_via_objects(self, user_alice):
        """Test that deleted users can be accessed via objects manager."""
        user_id = user_alice.id

        # Soft delete
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # Not in active manager
        assert not User.active.filter(id=user_id).exists()

        # But accessible via objects (default manager includes all)
        assert User.objects.filter(id=user_id).exists()

    def test_deleted_at_timestamp_preserved(self, user_alice):
        """Test that deleted_at timestamp is preserved accurately."""
        deletion_time = timezone.now()
        user_alice.deleted_at = deletion_time
        user_alice.save()

        user_alice.refresh_from_db()

        # Should be within 1 second (accounting for DB precision)
        assert abs((user_alice.deleted_at - deletion_time).total_seconds()) < 1

    def test_multiple_users_different_deletion_times(self, user_alice, user_bob):
        """Test that multiple users can have different deletion times."""
        time1 = timezone.now()
        time2 = time1 + timedelta(hours=1)

        user_alice.deleted_at = time1
        user_alice.save()

        user_bob.deleted_at = time2
        user_bob.save()

        user_alice.refresh_from_db()
        user_bob.refresh_from_db()

        assert user_alice.deleted_at != user_bob.deleted_at

    def test_active_manager_only_returns_active_users(self, user_alice, user_bob):
        """Test that active manager only returns active users."""
        # Both active initially
        assert User.active.count() == 2

        # Delete Alice
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # Only Bob in active manager
        assert User.active.count() == 1
        assert User.active.first().id == user_bob.id

    def test_objects_returns_all_users(self, user_alice, user_bob):
        """Test that objects manager returns all users including deleted."""
        # Delete Alice
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # objects includes both (no filtering by default)
        assert User.objects.count() == 2

    def test_deleted_user_can_be_retrieved_by_id_via_objects(self, user_alice):
        """Test that deleted user can be retrieved by ID via objects."""
        user_id = user_alice.id

        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # Can retrieve via objects
        deleted_user = User.objects.get(id=user_id)
        assert deleted_user.deleted_at is not None

    def test_filter_deleted_users_explicitly(self, user_alice, user_bob):
        """Test filtering deleted users explicitly."""
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # Filter deleted users
        deleted_users = User.objects.filter(deleted_at__isnull=False)
        assert deleted_users.count() == 1
        assert deleted_users.first().id == user_alice.id

    def test_filter_active_users_explicitly(self, user_alice, user_bob):
        """Test filtering active users explicitly via objects."""
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        # Filter active users via objects
        active_users = User.objects.filter(deleted_at__isnull=True)
        assert active_users.count() == 1
        assert active_users.first().id == user_bob.id

    def test_deleted_at_future_date_allowed(self, user_alice):
        """Test that deleted_at can be set to future date (for scheduled deletion)."""
        future_time = timezone.now() + timedelta(days=30)
        user_alice.deleted_at = future_time
        user_alice.save()

        user_alice.refresh_from_db()
        assert user_alice.deleted_at > timezone.now()

    def test_clearing_deleted_at_restores_user(self, user_alice):
        """Test that clearing deleted_at restores user to active manager."""
        user_id = user_alice.id

        # Soft delete
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        assert not User.active.filter(id=user_id).exists()

        # Restore by clearing deleted_at
        user_alice.deleted_at = None
        user_alice.save()

        assert User.active.filter(id=user_id).exists()

    def test_deleted_users_excluded_from_active_count(self, user_alice, user_bob):
        """Test that deleted users are excluded from active.count()."""
        assert User.active.count() == 2

        user_alice.deleted_at = timezone.now()
        user_alice.save()

        assert User.active.count() == 1

    def test_deleted_users_excluded_from_active_exists(self, user_alice):
        """Test that deleted users return False for active.exists()."""
        user_id = user_alice.id

        assert User.active.filter(id=user_id).exists() is True

        user_alice.deleted_at = timezone.now()
        user_alice.save()

        assert User.active.filter(id=user_id).exists() is False

    def test_get_deleted_user_via_active_raises_does_not_exist(self, user_alice):
        """Test that getting deleted user via active manager raises DoesNotExist."""
        user_id = user_alice.id

        user_alice.deleted_at = timezone.now()
        user_alice.save()

        with pytest.raises(User.DoesNotExist):
            User.active.get(id=user_id)

    def test_deleted_at_timezone_aware(self, user_alice):
        """Test that deleted_at is timezone-aware."""
        user_alice.deleted_at = timezone.now()
        user_alice.save()

        user_alice.refresh_from_db()

        # Should be timezone-aware (has tzinfo)
        assert user_alice.deleted_at.tzinfo is not None
