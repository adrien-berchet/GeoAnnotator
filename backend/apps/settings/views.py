"""
Views for user preferences API endpoints.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import UserPreferences
from .serializers import UserPreferencesSerializer


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_preferences_view(request):
    """
    GET /api/settings/ - Retrieve user preferences
    PATCH /api/settings/ - Update user preferences (partial)

    Returns:
        200: Success with UserPreferences data
        400: Validation error (PATCH only)
        401: Unauthenticated
        404: Preferences not found (GET only, shouldn't happen if signal is active)
    """

    if request.method == 'GET':
        # Retrieve user preferences
        preferences = get_object_or_404(UserPreferences, user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == 'PATCH':
        # Update user preferences (partial)
        preferences = get_object_or_404(UserPreferences, user=request.user)
        serializer = UserPreferencesSerializer(
            preferences,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
