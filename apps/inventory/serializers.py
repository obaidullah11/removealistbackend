"""
Serializers for inventory management.
"""
from rest_framework import serializers
from .models import InventoryRoom
from apps.moves.models import Move


class InventoryRoomCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating an inventory room.
    """
    
    class Meta:
        model = InventoryRoom
        fields = ['name', 'type', 'move_id']
    
    def validate_move_id(self, value):
        """Validate that the move belongs to the user."""
        user = self.context['request'].user
        try:
            move = Move.objects.get(id=value, user=user)
            return move
        except Move.DoesNotExist:
            raise serializers.ValidationError("Move not found or doesn't belong to you")
    
    def validate_type(self, value):
        """Validate room type choice."""
        valid_choices = [choice[0] for choice in InventoryRoom.ROOM_TYPE_CHOICES]
        if value not in valid_choices:
            raise serializers.ValidationError(f"Invalid room type. Choose from: {', '.join(valid_choices)}")
        return value
    
    def create(self, validated_data):
        """Create an inventory room."""
        move = validated_data.pop('move_id')
        return InventoryRoom.objects.create(move=move, **validated_data)


class InventoryRoomUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating an inventory room.
    """
    
    class Meta:
        model = InventoryRoom
        fields = ['name', 'items', 'boxes', 'heavy_items', 'packed']
    
    def validate_items(self, value):
        """Validate items list."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Items must be a list")
        
        # Validate each item is a string
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Each item must be a string")
            if len(item.strip()) == 0:
                raise serializers.ValidationError("Items cannot be empty strings")
        
        return value
    
    def validate_boxes(self, value):
        """Validate boxes count."""
        if value < 0:
            raise serializers.ValidationError("Boxes count cannot be negative")
        return value
    
    def validate_heavy_items(self, value):
        """Validate heavy items count."""
        if value < 0:
            raise serializers.ValidationError("Heavy items count cannot be negative")
        return value


class InventoryRoomDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory room details.
    """
    total_items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryRoom
        fields = [
            'id', 'name', 'type', 'items', 'boxes', 'heavy_items',
            'image', 'packed', 'total_items_count', 'move_id', 'created_at'
        ]
        read_only_fields = ['id', 'move_id', 'created_at', 'total_items_count']


class InventoryRoomListSerializer(serializers.ModelSerializer):
    """
    Serializer for inventory room list (summary view).
    """
    total_items_count = serializers.ReadOnlyField()
    
    class Meta:
        model = InventoryRoom
        fields = [
            'id', 'name', 'type', 'boxes', 'heavy_items',
            'packed', 'total_items_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'total_items_count']


class RoomPackedSerializer(serializers.ModelSerializer):
    """
    Serializer for marking room as packed/unpacked.
    """
    
    class Meta:
        model = InventoryRoom
        fields = ['packed']


class RoomImageUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for room image upload.
    """
    
    class Meta:
        model = InventoryRoom
        fields = ['image']
    
    def validate_image(self, value):
        """Validate image file."""
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size exceeds 10MB limit")
        
        # Check file format
        allowed_formats = ['jpeg', 'jpg', 'png']
        file_extension = value.name.lower().split('.')[-1]
        if file_extension not in allowed_formats:
            raise serializers.ValidationError("Unsupported file format. Please use PNG, JPG, or JPEG")
        
        return value
