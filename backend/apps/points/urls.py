"""
Points app URL configuration.
"""

from django.urls import path

from . import views

app_name = "points"

urlpatterns = [
    # GPS Points CRUD
    path("", views.GPSPointViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path(
        "<uuid:pk>/",
        views.GPSPointViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="detail",
    ),
    # Search endpoints
    path(
        "search/bbox/", views.GPSPointViewSet.as_view({"post": "search_bbox"}), name="search-bbox"
    ),
    path(
        "search/tags/", views.GPSPointViewSet.as_view({"post": "search_tags"}), name="search-tags"
    ),
    path("search/text/", views.GPSPointViewSet.as_view({"get": "search_text"}), name="search-text"),
    path(
        "search/nearby/",
        views.GPSPointViewSet.as_view({"post": "search_nearby"}),
        name="search-nearby",
    ),
    # Lock management
    path(
        "<uuid:pk>/lock/",
        views.GPSPointViewSet.as_view({"post": "acquire_lock", "delete": "release_lock"}),
        name="lock",
    ),
]
