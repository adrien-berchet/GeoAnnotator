from django.contrib import admin
from .models import Annotation

@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('gps_point', 'type', 'file_name', 'created_at')
    list_filter = ('type',)
    search_fields = ('gps_point__title', 'file_name')
