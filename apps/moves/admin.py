"""
Admin configuration for move models.
"""
from django.contrib import admin
from .models import Move


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    """
    Admin configuration for Move model.
    """
    list_display = [
        'user', 'move_date', 'current_location', 'destination_location',
        'from_property_type', 'to_property_type', 'status', 'progress', 'created_at'
    ]
    list_filter = ['status', 'from_property_type', 'from_property_size', 'to_property_type', 'to_property_size', 'move_date', 'created_at']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'current_location', 'destination_location', 'first_name', 'last_name'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'progress']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'move_date', 'status', 'progress')
        }),
        ('Locations', {
            'fields': ('current_location', 'destination_location')
        }),
        ('Property Details', {
            'fields': ('from_property_type', 'from_property_size', 'to_property_type', 'to_property_size', 'special_items', 'additional_details')
        }),
        ('Contact Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
