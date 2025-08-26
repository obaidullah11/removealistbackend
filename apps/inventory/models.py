"""
Models for inventory management.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from apps.moves.models import Move
from apps.common.utils import ChoicesMixin
from apps.common.validators import validate_image_file

User = get_user_model()


class InventoryRoom(models.Model, ChoicesMixin):
    """
    Model representing a room in the inventory.
    """
    
    ROOM_TYPE_CHOICES = [
        ('living_room', 'Living Room'),
        ('kitchen', 'Kitchen'),
        ('bedroom', 'Bedroom'),
        ('bathroom', 'Bathroom'),
        ('office', 'Office'),
        ('garage', 'Garage'),
        ('basement', 'Basement'),
        ('attic', 'Attic'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    move = models.ForeignKey(Move, on_delete=models.CASCADE, related_name='inventory_rooms')
    
    # Room details
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    items = models.JSONField(default=list, blank=True)  # List of item names
    boxes = models.IntegerField(default=0)
    heavy_items = models.IntegerField(default=0)
    image = models.ImageField(
        upload_to='room_images/', 
        null=True, 
        blank=True,
        validators=[validate_image_file]
    )
    packed = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_rooms'
        verbose_name = 'Inventory Room'
        verbose_name_plural = 'Inventory Rooms'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()}) - {self.move}"
    
    def save(self, *args, **kwargs):
        """Update move progress when room is saved."""
        super().save(*args, **kwargs)
        # Trigger progress calculation for the move
        if hasattr(self.move, 'calculate_progress'):
            self.move.calculate_progress()
    
    @property
    def total_items_count(self):
        """Get total count of items in the room."""
        return len(self.items) + self.boxes + self.heavy_items
