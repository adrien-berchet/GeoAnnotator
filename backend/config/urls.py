"""
URL configuration for GeoAnnotator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include
from django.urls import path


def admin_redirect(request):  # noqa: ARG001
    return redirect("/admin/")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("admin_redirect/", admin_redirect, name="admin_redirect"),
    # API v1 endpoints
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/points/", include("apps.points.urls")),
    path("api/v1/points/<uuid:point_id>/annotations/", include("apps.annotations.urls")),
    path("api/v1/points/<uuid:point_id>/sharing/", include("apps.sharing.urls")),
    path("api/v1/sharing/", include("apps.sharing.global_urls")),
    path("api/v1/", include("apps.export_import.urls")),
    path("api/v1/trash/", include("apps.trash.urls")),
    path("api/v1/tags/", include("apps.points.tags_urls")),
    path("api/v1/types/", include("apps.points.types_urls")),
    path("api/v1/settings/", include("apps.settings.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
