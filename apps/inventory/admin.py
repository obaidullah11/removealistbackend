"""
Admin configuration for inventory models.
"""
from django.contrib import admin
from .models import InventoryRoom


@admin.register(InventoryRoom)
class InventoryRoomAdmin(admin.ModelAdmin):
    """
    Admin configuration for InventoryRoom model.
    """
    list_display = [
        'name', 'type', 'move', 'boxes', 'heavy_items',
        'packed', 'total_items_count', 'created_at'
    ]
    list_filter = ['type', 'packed', 'created_at']
    search_fields = [
        'name', 'move__user__email', 'move__current_location',
        'move__destination_location'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'total_items_count']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Room Information', {
            'fields': ('move', 'name', 'type', 'packed')
        }),
        ('Inventory Details', {
            'fields': ('items', 'boxes', 'heavy_items', 'total_items_count')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('move', 'move__user')
