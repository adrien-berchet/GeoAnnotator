"""
Django signals for sharing app.

Handles automatic unsharing when users are soft-deleted.
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.authentication.models import User

from .models import Share


@receiver(pre_save, sender=User)
def unshare_content_on_delete(sender, instance, **kwargs):
    """
    Automatically unshare all user's content when account is soft-deleted.

    This signal fires before saving a User model. If deleted_at is being set
    (user is being soft-deleted), all their active shares are deactivated.

    Args:
        sender: The User model class
        instance: The User instance being saved
        **kwargs: Additional keyword arguments
    """
    # Only proceed if this is an update (not a new user creation)
    if instance.pk is None:
        return

    try:
        # Get the previous state of the user from database
        old_instance = User.objects.get(pk=instance.pk)

        # Check if deleted_at is being set (transitioning from None to a timestamp)
        if old_instance.deleted_at is None and instance.deleted_at is not None:
            # User is being soft-deleted, unshare all their content
            Share.objects.filter(owner=instance, is_active=True).update(is_active=False)

    except User.DoesNotExist:
        # This shouldn't happen, but handle gracefully
        pass
