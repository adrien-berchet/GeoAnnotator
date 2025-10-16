"""
Signals for settings app.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserPreferences

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Auto-create UserPreferences with default values when a new user is created.

    This signal ensures that every user has preferences immediately after registration.
    """
    if created:
        UserPreferences.objects.create(user=instance)
