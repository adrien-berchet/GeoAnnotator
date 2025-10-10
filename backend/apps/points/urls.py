"""
Points app URL configuration.
"""
from django.urls import path
from . import views

app_name = 'points'

urlpatterns = [
    # GPS Points CRUD
    path('', views.GPSPointViewSet.as_view({'get': 'list', 'post': 'create'}), name='list'),
    path('<uuid:pk>/', views.GPSPointViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='detail'),

    # Lock management
    path('<uuid:pk>/lock/', views.GPSPointViewSet.as_view({'post': 'acquire_lock', 'delete': 'release_lock'}), name='lock'),
]
