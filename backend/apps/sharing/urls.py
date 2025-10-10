"""
Sharing nested URLs (under points).
"""
from django.urls import path
from . import views

app_name = 'sharing'

# Nested routes - list/create shares for a point
urlpatterns = [
    path('', views.ShareViewSet.as_view({'get': 'list', 'post': 'create'}), name='list'),
    # path('<uuid:pk>/', views.ShareViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='detail'),

    # # Global share actions
    # path('received/', views.ShareViewSet.as_view({'get': 'received'}), name='received'),
    # path('accept/<uuid:token>/', views.ShareViewSet.as_view({'post': 'accept'}), name='accept'),
]
