"""
Views for inventory management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import InventoryRoom
from .serializers import (
    InventoryRoomCreateSerializer, InventoryRoomUpdateSerializer,
    InventoryRoomDetailSerializer, InventoryRoomListSerializer,
    RoomPackedSerializer, RoomImageUploadSerializer
)
from apps.moves.models import Move
from apps.common.utils import success_response, error_response, paginated_response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_rooms(request):
    """
    Get inventory rooms for a specific move.
    """
    move_id = request.GET.get('move_id')
    
    if not move_id:
        return error_response(
            "Move ID required",
            {'move_id': ['This parameter is required']},
            status.HTTP_400_BAD_REQUEST
        )
    
    # Verify move belongs to user
    move = get_object_or_404(Move, id=move_id, user=request.user)
    
    # Get rooms for this move
    rooms = InventoryRoom.objects.filter(move=move)
    
    # Check if pagination is requested
    if request.GET.get('page'):
        return paginated_response(
            rooms,
            InventoryRoomListSerializer,
            request,
            "Rooms retrieved successfully"
        )
    
    # Return all rooms without pagination
    serializer = InventoryRoomDetailSerializer(rooms, many=True)
    
    return success_response(
        "Rooms retrieved successfully",
        serializer.data
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_room(request):
    """
    Create a new inventory room.
    """
    serializer = InventoryRoomCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        room = serializer.save()
        
        # Return detailed room data
        detail_serializer = InventoryRoomDetailSerializer(room)
        
        return success_response(
            "Room created successfully",
            detail_serializer.data,
            status.HTTP_201_CREATED
        )
    
    return error_response(
        "Room creation failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_room(request, room_id):
    """
    Get room details by ID.
    """
    room = get_object_or_404(InventoryRoom, id=room_id, move__user=request.user)
    
    serializer = InventoryRoomDetailSerializer(room)
    
    return success_response(
        "Room details retrieved",
        serializer.data
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_room(request, room_id):
    """
    Update an inventory room.
    """
    room = get_object_or_404(InventoryRoom, id=room_id, move__user=request.user)
    
    serializer = InventoryRoomUpdateSerializer(room, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        # Return updated room data
        detail_serializer = InventoryRoomDetailSerializer(room)
        
        return success_response(
            "Room updated successfully",
            detail_serializer.data
        )
    
    return error_response(
        "Room update failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def mark_room_packed(request, room_id):
    """
    Mark room as packed or unpacked.
    """
    room = get_object_or_404(InventoryRoom, id=room_id, move__user=request.user)
    
    serializer = RoomPackedSerializer(room, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        # Return updated room data
        detail_serializer = InventoryRoomDetailSerializer(room)
        
        return success_response(
            "Room packing status updated",
            detail_serializer.data
        )
    
    return error_response(
        "Failed to update packing status",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_room(request, room_id):
    """
    Delete an inventory room.
    """
    room = get_object_or_404(InventoryRoom, id=room_id, move__user=request.user)
    
    room.delete()
    
    return success_response("Room deleted successfully")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_room_image(request, room_id):
    """
    Upload image for an inventory room.
    """
    room = get_object_or_404(InventoryRoom, id=room_id, move__user=request.user)
    
    serializer = RoomImageUploadSerializer(room, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        return success_response(
            "Room image uploaded successfully",
            {
                'id': str(room.id),
                'image': room.image.url if room.image else None
            }
        )
    
    return error_response(
        "Image upload failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )
