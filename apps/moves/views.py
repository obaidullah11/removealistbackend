"""
Views for move management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Move
from .serializers import (
    MoveCreateSerializer, MoveUpdateSerializer, 
    MoveDetailSerializer, MoveListSerializer
)
from apps.common.utils import success_response, error_response, paginated_response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_move(request):
    """
    Create a new move.
    """
    serializer = MoveCreateSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        move = serializer.save()
        
        # Return detailed move data
        detail_serializer = MoveDetailSerializer(move)
        
        return success_response(
            "Move created successfully",
            detail_serializer.data,
            status.HTTP_201_CREATED
        )
    
    return error_response(
        "Move creation failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_move(request, move_id):
    """
    Get move details by ID.
    """
    move = get_object_or_404(Move, id=move_id, user=request.user)
    
    # Update progress before returning
    move.calculate_progress()
    
    serializer = MoveDetailSerializer(move)
    
    return success_response(
        "Move details retrieved",
        serializer.data
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_moves(request):
    """
    Get all moves for the authenticated user.
    """
    moves = Move.objects.filter(user=request.user)
    
    # Update progress for all moves
    for move in moves:
        move.calculate_progress()
    
    # Check if pagination is requested
    if request.GET.get('page'):
        return paginated_response(
            moves, 
            MoveListSerializer, 
            request, 
            "Moves retrieved successfully"
        )
    
    # Return all moves without pagination
    serializer = MoveListSerializer(moves, many=True)
    
    return success_response(
        "Moves retrieved successfully",
        serializer.data
    )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_move(request, move_id):
    """
    Update a move.
    """
    move = get_object_or_404(Move, id=move_id, user=request.user)
    
    serializer = MoveUpdateSerializer(move, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        # Return updated move data
        detail_serializer = MoveDetailSerializer(move)
        
        return success_response(
            "Move updated successfully",
            detail_serializer.data
        )
    
    return error_response(
        "Move update failed",
        serializer.errors,
        status.HTTP_400_BAD_REQUEST
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_move(request, move_id):
    """
    Delete a move.
    """
    move = get_object_or_404(Move, id=move_id, user=request.user)
    
    # Check if move can be deleted (not in progress or completed)
    if move.status in ['in_progress', 'completed']:
        return error_response(
            "Cannot delete move",
            {'detail': ['Cannot delete a move that is in progress or completed']},
            status.HTTP_400_BAD_REQUEST
        )
    
    move.delete()
    
    return success_response("Move deleted successfully")
