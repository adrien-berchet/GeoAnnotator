from django.contrib import admin
from .models import GPSPoint, PointType, Tag

@admin.register(GPSPoint)
class GPSPointAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'latitude', 'longitude', 'is_public', 'created_at')
    list_filter = ('is_public',)
    search_fields = ('title', 'owner__email')

@admin.register(PointType)
class PointTypeAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'type_choice', 'visibility', 'status', 'owner')
    list_filter = ('type_choice', 'visibility', 'status')
    search_fields = ('names', 'owner__email')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
