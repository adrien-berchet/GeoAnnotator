"""
URL configuration for settings app.
"""
from django.urls import path
from .views import user_preferences_view

app_name = 'settings'

urlpatterns = [
    path('', user_preferences_view, name='user-preferences'),
]
