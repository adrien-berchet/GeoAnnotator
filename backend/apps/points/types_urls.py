"""
Point Types URL configuration.
"""
from django.urls import path
from . import views

app_name = 'point-types'

urlpatterns = [
    # Point Types CRUD
    path('', views.PointTypeViewSet.as_view({'get': 'list', 'post': 'create'}), name='list'),
    path('<uuid:pk>/', views.PointTypeViewSet.as_view({
        'get': 'retrieve',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='detail'),

    # Reorder endpoint
    path('reorder/', views.PointTypeViewSet.as_view({'post': 'reorder'}), name='reorder'),

    # Upload icon endpoint
    path('upload-icon/', views.PointTypeViewSet.as_view({'post': 'upload_icon'}), name='upload-icon'),
]
