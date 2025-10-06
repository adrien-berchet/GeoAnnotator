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
    # API endpoints will be added here as apps are created
    # path('api/v1/auth/', include('apps.authentication.urls')),
    # path('api/v1/', include('apps.points.urls')),
    # path('api/v1/', include('apps.annotations.urls')),
    # path('api/v1/', include('apps.sharing.urls')),
    # path('api/v1/', include('apps.export_import.urls')),
    # path('api/v1/', include('apps.trash.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
