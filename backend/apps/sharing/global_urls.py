"""
All sharing URLs (global routes not nested under points).
"""
from django.urls import path
from . import views

app_name = 'global_sharing'

urlpatterns = [
    # Global routes: accessible by share ID directly
    path('<uuid:pk>/', views.ShareViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='detail'),

    # Global share actions
    path('received/', views.ShareViewSet.as_view({'get': 'received'}), name='received'),
    path('accept/<uuid:token>/', views.ShareViewSet.as_view({'post': 'accept'}), name='accept'),
]
