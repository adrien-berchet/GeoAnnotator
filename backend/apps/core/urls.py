"""
URLs for core utility endpoints.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("email-config/", views.email_config_status, name="email-config-status"),
]
