"""
Trash app URL configuration.
"""
from django.urls import path
from . import views

app_name = 'trash'

urlpatterns = [
    path('', views.TrashViewSet.as_view({'get': 'list'}), name='trash-list'),
    path('<uuid:pk>/restore/', views.TrashViewSet.as_view({'post': 'restore'}), name='trash-restore'),
    path('<uuid:pk>/permanent/', views.TrashViewSet.as_view({'delete': 'permanent_delete'}), name='trash-permanent'),
    path('empty/', views.TrashViewSet.as_view({'delete': 'empty'}), name='trash-empty'),
]
