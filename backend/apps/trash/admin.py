from django.contrib import admin
from .models import Trash, AnnotationTrash

@admin.register(Trash)
class TrashAdmin(admin.ModelAdmin):
    list_display = ('gps_point', 'deleted_by', 'deleted_at', 'permanent_deletion_at')
    search_fields = ('gps_point__title', 'deleted_by__email')

@admin.register(AnnotationTrash)
class AnnotationTrashAdmin(admin.ModelAdmin):
    list_display = ('annotation', 'deleted_by', 'deleted_at', 'permanent_deletion_at')
    search_fields = ('annotation__id', 'deleted_by__email')
