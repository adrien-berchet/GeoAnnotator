"""
All sharing URLs (global routes not nested under points).
"""
from django.urls import path
from . import views

app_name = 'sharing_global'

urlpatterns = [
    # Global routes: accessible by share ID directly
    path('<uuid:pk>/', views.ShareViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='share-detail'),

    # Global share actions
    path('received/', views.ShareViewSet.as_view({'get': 'received'}), name='share-received'),
    path('accept/<uuid:token>/', views.ShareViewSet.as_view({'post': 'accept'}), name='share-accept'),
]
