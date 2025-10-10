"""
Export/Import app URL configuration.
"""
from django.urls import path
from . import views

app_name = 'export_import'

urlpatterns = [
    path('export/', views.export_view, name='export'),
    path('import/', views.import_view, name='import'),
]
