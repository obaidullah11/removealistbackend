"""
Models for move management.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.common.validators import validate_future_date
from apps.common.utils import ChoicesMixin

User = get_user_model()


class Move(models.Model, ChoicesMixin):
    """
    Model representing a user's move.
    """
    
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('townhouse', 'Townhouse'),
        ('office', 'Office'),
        ('storage', 'Storage'),
        ('other', 'Other'),
    ]
    
    PROPERTY_SIZE_CHOICES = [
        ('studio', 'Studio'),
        ('1bedroom', '1 Bedroom'),
        ('2bedroom', '2 Bedroom'),
        ('3bedroom', '3 Bedroom'),
        ('4bedroom', '4+ Bedroom'),
        ('small_office', 'Small Office'),
        ('medium_office', 'Medium Office'),
        ('large_office', 'Large Office'),
    ]
    
    STATUS_CHOICES = [
        ('planning', 'Planning'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='moves')
    
    # Move details
    move_date = models.DateField(validators=[validate_future_date])
    current_location = models.TextField()
    destination_location = models.TextField()
    from_property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    from_property_size = models.CharField(max_length=20, choices=PROPERTY_SIZE_CHOICES)
    to_property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    to_property_size = models.CharField(max_length=20, choices=PROPERTY_SIZE_CHOICES)
    special_items = models.TextField(blank=True, null=True)
    additional_details = models.TextField(blank=True, null=True)
    
    # Contact info (can be different from user's info)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planning')
    progress = models.IntegerField(default=0)  # Percentage (0-100)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'moves'
        verbose_name = 'Move'
        verbose_name_plural = 'Moves'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Move from {self.current_location} to {self.destination_location} on {self.move_date}"
    
    def calculate_progress(self):
        """
        Calculate move progress based on completed tasks and checklist items.
        """
        # This will be implemented when we have timeline and checklist models
        total_tasks = 0
        completed_tasks = 0
        
        # Count timeline events
        if hasattr(self, 'timeline_events'):
            timeline_events = self.timeline_events.all()
            total_tasks += timeline_events.count()
            completed_tasks += timeline_events.filter(completed=True).count()
        
        # Count checklist items
        if hasattr(self, 'checklist_items'):
            checklist_items = self.checklist_items.all()
            total_tasks += checklist_items.count()
            completed_tasks += checklist_items.filter(completed=True).count()
        
        # Count inventory rooms (if packed)
        if hasattr(self, 'inventory_rooms'):
            rooms = self.inventory_rooms.all()
            total_tasks += rooms.count()
            completed_tasks += rooms.filter(packed=True).count()
        
        if total_tasks > 0:
            progress = int((completed_tasks / total_tasks) * 100)
            self.progress = min(progress, 100)
            self.save(update_fields=['progress'])
        
        return self.progress
    
    @property
    def is_upcoming(self):
        """Check if the move is upcoming (within 30 days)."""
        return (self.move_date - timezone.now().date()).days <= 30
    
    @property
    def days_until_move(self):
        """Get days until move date."""
        return (self.move_date - timezone.now().date()).days
