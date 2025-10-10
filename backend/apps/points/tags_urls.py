"""
Tags URL configuration.
"""
from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.TagViewSet.as_view({'get': 'list'}), name='list'),
]
