"""
Annotations app URL configuration (nested under points).
"""
from django.urls import path
from . import views

app_name = 'annotations'

urlpatterns = [
    # Annotations for a specific point (requires point_id in URL)
    path('', views.AnnotationViewSet.as_view({'get': 'list', 'post': 'create'}), name='annotation-list'),
    path('<uuid:pk>/', views.AnnotationViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='annotation-detail'),
    path('<uuid:pk>/download/', views.AnnotationViewSet.as_view({'get': 'download'}), name='annotation-download'),
]
