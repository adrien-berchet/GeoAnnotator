"""
Trash app URL configuration.
"""
from django.urls import path
from . import views

app_name = 'trash'

urlpatterns = [
    # Point trash endpoints
    path('points/', views.TrashViewSet.as_view({'get': 'list'}), name='points-list'),
    path('points/<uuid:pk>/restore/', views.TrashViewSet.as_view({'post': 'restore'}), name='points-restore'),
    path('points/<uuid:pk>/permanent/', views.TrashViewSet.as_view({'delete': 'permanent_delete'}), name='points-permanent'),
    path('points/empty/', views.TrashViewSet.as_view({'delete': 'empty'}), name='points-empty'),
    path('points/stats/', views.TrashViewSet.as_view({'get': 'stats'}), name='points-stats'),

    # Annotation trash endpoints
    path('annotations/', views.AnnotationTrashViewSet.as_view({'get': 'list'}), name='annotations-list'),
    path('annotations/<uuid:pk>/restore/', views.AnnotationTrashViewSet.as_view({'post': 'restore'}), name='annotations-restore'),
    path('annotations/<uuid:pk>/permanent/', views.AnnotationTrashViewSet.as_view({'delete': 'permanent_delete'}), name='annotations-permanent'),
    path('annotations/empty/', views.AnnotationTrashViewSet.as_view({'delete': 'empty'}), name='annotations-empty'),
    path('annotations/stats/', views.AnnotationTrashViewSet.as_view({'get': 'stats'}), name='annotations-stats'),
]
