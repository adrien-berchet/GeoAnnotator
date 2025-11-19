"""
All sharing URLs (global routes not nested under points).
"""

from django.urls import path

from . import views

app_name = "global_sharing"

urlpatterns = [
    # Global routes: accessible by share ID directly
    path(
        "<uuid:pk>/",
        views.ShareViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="detail",
    ),
    # Global share actions
    path("received/", views.ShareViewSet.as_view({"get": "received"}), name="received"),
    path("accept/<uuid:token>/", views.ShareViewSet.as_view({"post": "accept"}), name="accept"),
]

# Friendship URLs - accessible at /api/v1/sharing/friendships/
friendship_urlpatterns = [
    path(
        "friendships/",
        views.FriendshipViewSet.as_view({"get": "list", "post": "create"}),
        name="friendship-list",
    ),
    path(
        "friendships/<uuid:pk>/",
        views.FriendshipViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="friendship-detail",
    ),
]

# Batch sharing URL - accessible at /api/v1/sharing/batch/
batch_urlpatterns = [
    path(
        "batch/",
        views.BatchShareView.as_view({"post": "create"}),
        name="batch-share",
    ),
]

# Combine all patterns
urlpatterns = urlpatterns + friendship_urlpatterns + batch_urlpatterns
