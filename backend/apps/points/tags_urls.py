"""
Tags URL configuration.
"""
from django.urls import path
from . import views

app_name = 'tags'

urlpatterns = [
    path('', views.TagViewSet.as_view({'get': 'list', 'post': 'create'}), name='list'),
    path('<uuid:pk>/', views.TagViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='detail'),
]
