"""
URL configuration for GeoAnnotator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/auth/', include('apps.authentication.urls')),
    path('api/points/', include('apps.points.urls')),
    path('api/points/<uuid:point_id>/annotations/', include('apps.annotations.urls')),
    path('api/points/<uuid:point_id>/sharing/', include('apps.sharing.urls')),
    # path('api/shares/', include(('apps.sharing.global_urls', 'shares'))),
    # path('api/sharing/', include('apps.sharing.urls')),
    path('api/sharing/', include('apps.sharing.global_urls')),
    path('api/', include('apps.export_import.urls')),
    path('api/trash/', include('apps.trash.urls')),

    # Tags endpoint
    path('api/tags/', include('apps.points.tags_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
