"""
GPS Point views for CRUD operations and spatial search.
"""
from datetime import timedelta
import os
import uuid as uuid_lib
import requests
from io import BytesIO
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from django.db.models import Q
from django.core.files.storage import default_storage
from django.conf import settings

from .models import GPSPoint, PointType
from .serializers import (
    GPSPointSerializer, CreateGPSPointSerializer, UpdateGPSPointSerializer,
    PointTypeSerializer, CreatePointTypeSerializer, PointTypeReorderSerializer
)
from .services import PointService, EditingLockService
from apps.sharing.services import PermissionService


class GPSPointViewSet(viewsets.ModelViewSet):
    """
    ViewSet for GPS Point CRUD operations and spatial search.

    Endpoints:
    - GET /api/points/ - List user's accessible points
    - POST /api/points/ - Create new point
    - GET /api/points/{id}/ - Retrieve point detail
    - PUT/PATCH /api/points/{id}/ - Update point
    - DELETE /api/points/{id}/ - Delete point (move to trash)
    - POST /api/points/search/bbox/ - Search by bounding box
    - POST /api/points/search/nearby/ - Search by radius
    - POST /api/points/search/tags/ - Search by tags
    - GET /api/points/search/text/?q=... - Full-text search
    - POST /api/points/{id}/acquire-lock/ - Acquire editing lock
    - POST /api/points/{id}/release-lock/ - Release editing lock
    - GET /api/points/{id}/lock-status/ - Get lock status
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateGPSPointSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateGPSPointSerializer
        return GPSPointSerializer

    def get_queryset(self):
        """Return points accessible to current user with optional search filtering."""
        user = self.request.user
        queryset = PermissionService.get_accessible_points(user, include_public=True)

        # Apply search filter if provided
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()

        return queryset

    def create(self, request):
        """Create new GPS point."""
        serializer = CreateGPSPointSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Create point via service
        point = PointService.create_point(
            title=serializer.validated_data['title'],
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            owner=request.user,
            description=serializer.validated_data.get('description', ''),
            is_public=serializer.validated_data.get('is_public', False),
            tags=serializer.validated_data.get('tags', []),
            point_type=serializer.validated_data.get('type_id')
        )

        # Return created point
        response_serializer = GPSPointSerializer(point, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Get point detail."""
        # Get point without permission filter to distinguish 404 from 403
        try:
            point = GPSPoint.objects.get(pk=pk)
        except GPSPoint.DoesNotExist:
            raise NotFound('Point not found')

        # Check if point is trashed
        if hasattr(point, 'trash_entry') and point.trash_entry:
            raise NotFound('Point not found')

        # Check view permission
        if not PermissionService.can_view(point, request.user):
            raise PermissionDenied('You do not have permission to view this point')

        serializer = GPSPointSerializer(point, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None, partial=False):
        """Update GPS point."""
        # Get point without permission filter to distinguish 404 from 403
        try:
            point = GPSPoint.objects.get(pk=pk)
        except GPSPoint.DoesNotExist:
            raise NotFound('Point not found')

        # Check edit permission
        if not PermissionService.can_edit(point, request.user):
            raise PermissionDenied('You do not have permission to edit this point')

        # Check if point is locked by another user
        if EditingLockService.is_locked(point) and point.editing_lock_user != request.user:
            lock_info = EditingLockService.get_lock_info(point)
            return Response(
                {
                    'error': 'Point is currently locked by another user',
                    'locked_by': lock_info['locked_by'].email if lock_info else None,
                    'lock_expires_at': lock_info['lock_expires_at'].isoformat() if lock_info and lock_info.get('lock_expires_at') else None
                },
                status=status.HTTP_409_CONFLICT
            )

        serializer = UpdateGPSPointSerializer(data=request.data, partial=partial, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Update via service (handles locking)
        updated_point = PointService.update_point(
            point=point,
            user=request.user,
            **serializer.validated_data
        )

        response_serializer = GPSPointSerializer(updated_point, context={'request': request})
        return Response(response_serializer.data)

    def partial_update(self, request, pk=None):
        """Partial update GPS point."""
        return self.update(request, pk, partial=True)

    def destroy(self, request, pk=None):
        """Delete GPS point (move to trash)."""
        # Get point without permission filter to distinguish 404 from 403
        try:
            point = GPSPoint.objects.get(pk=pk)
        except GPSPoint.DoesNotExist:
            raise NotFound('Point not found')

        # Check if owner (only owner can delete)
        if not PermissionService.is_owner(point, request.user):
            raise PermissionDenied('Only the owner can delete this point')

        # Delete via service (moves to trash)
        PointService.delete_point(point, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='search/bbox')
    def search_bbox(self, request):
        """Search points within bounding box."""
        min_lon = request.data.get('min_longitude')
        min_lat = request.data.get('min_latitude')
        max_lon = request.data.get('max_longitude')
        max_lat = request.data.get('max_latitude')

        if None in [min_lon, min_lat, max_lon, max_lat]:
            return Response(
                {'error': 'Missing required parameters: min/max latitude/longitude'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            points = PointService.search_points_by_bbox(
                min_lon=float(min_lon),
                min_lat=float(min_lat),
                max_lon=float(max_lon),
                max_lat=float(max_lat),
                user=request.user
            )

            serializer = GPSPointSerializer(points, many=True, context={'request': request})
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='search/nearby')
    def search_nearby(self, request):
        """Search points within radius."""
        lat = request.data.get('latitude')
        lon = request.data.get('longitude')
        radius = request.data.get('radius_meters', 1000)  # Default 1km

        if lat is None or lon is None:
            return Response(
                {'error': 'Missing required parameters: latitude, longitude'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            points = PointService.search_points_nearby(
                latitude=float(lat),
                longitude=float(lon),
                radius_meters=float(radius),
                user=request.user
            )

            serializer = GPSPointSerializer(points, many=True, context={'request': request})
            return Response(serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='search/tags')
    def search_tags(self, request):
        """Search points by tags."""
        tag_names = request.data.get('tags', [])

        if not tag_names or not isinstance(tag_names, list):
            return Response(
                {'error': 'Tags must be a non-empty array'},
                status=status.HTTP_400_BAD_REQUEST
            )

        points = PointService.search_points_by_tags(
            tag_names=tag_names,
            user=request.user
        )

        serializer = GPSPointSerializer(points, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='search/text')
    def search_text(self, request):
        """Full-text search in title/description."""
        search_text = request.query_params.get('q', '')

        if not search_text:
            return Response(
                {'error': 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        points = PointService.search_points_by_text(
            search_text=search_text,
            user=request.user
        )

        serializer = GPSPointSerializer(points, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='lock')
    def acquire_lock(self, request, pk=None):
        """Acquire editing lock on point."""
        point = self.get_object()

        # Check edit permission
        if not PermissionService.can_edit(point, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Acquire lock
        lock_acquired = EditingLockService.acquire_lock(point, request.user)

        if not lock_acquired:
            lock_info = EditingLockService.get_lock_info(point)
            return Response(
                {
                    'error': 'Point is currently locked',
                    'locked_by': lock_info['locked_by'].email if lock_info else None,
                    'lock_expires_at': lock_info['lock_expires_at'].isoformat() if lock_info and lock_info.get('lock_expires_at') else None
                },
                status=status.HTTP_409_CONFLICT
            )

        # Calculate lock expiry time
        lock_expires_at = point.editing_lock_acquired_at + timedelta(minutes=EditingLockService.LOCK_DURATION_MINUTES)

        return Response({
            'locked_by': {
                'id': str(request.user.id),
                'email': request.user.email
            },
            'acquired_at': point.editing_lock_acquired_at.isoformat(),
            'expires_at': lock_expires_at.isoformat()
        })

    @action(detail=True, methods=['delete'], url_path='lock')
    def release_lock(self, request, pk=None):
        """Release editing lock on point."""
        point = self.get_object()

        # Check if user can release lock
        # Either the user holds the lock, or the user is the owner (force-release)
        if point.editing_lock_user and point.editing_lock_user != request.user:
            # Check if user is owner (can force-release)
            if point.owner != request.user:
                return Response(
                    {'error': 'You cannot release a lock held by another user'},
                    status=status.HTTP_403_FORBIDDEN
                )
            # Owner can force-release
            point.editing_lock_user = None
            point.editing_lock_acquired_at = None
            point.save()
        else:
            # User holds the lock or no lock exists
            EditingLockService.release_lock(point, request.user)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='lock-status')
    def lock_status(self, request, pk=None):
        """Get current lock status."""
        point = self.get_object()

        is_locked = EditingLockService.is_locked(point)

        if is_locked:
            lock_info = EditingLockService.get_lock_info(point)
            return Response({
                'is_locked': True,
                'locked_by': lock_info['locked_by'].email,
                'lock_expires_at': lock_info['lock_expires_at'].isoformat()
            })

        return Response({'is_locked': False})


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tags (CRUD operations).

    Endpoints:
    - GET /api/tags/ - List all tags
    - POST /api/tags/ - Create new tag
    - GET /api/tags/{id}/ - Get tag detail
    - PUT/PATCH /api/tags/{id}/ - Update tag
    - DELETE /api/tags/{id}/ - Delete tag
    """
    from .models import Tag
    from .serializers import TagSerializer

    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for tags

    def get_queryset(self):
        """Filter tags by search query if provided."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)

        if search:
            queryset = queryset.filter(name__istartswith=search)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create new tag with proper error handling for duplicates."""
        from django.db import IntegrityError

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except IntegrityError:
            # Handle duplicate tag name
            tag_name = request.data.get('name', '')
            return Response(
                {'name': [f'Tag with name "{tag_name}" already exists.']},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete a tag.

        The tag will be removed from all points that use it.
        """
        tag = self.get_object()
        tag.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PointTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PointType CRUD operations and reordering.

    Endpoints:
    - GET /api/point-types/ - List user's point types (includes base types)
    - POST /api/point-types/ - Create new point type
    - GET /api/point-types/{id}/ - Retrieve point type detail
    - PATCH /api/point-types/{id}/ - Update point type
    - DELETE /api/point-types/{id}/ - Delete point type (soft delete, switches points to default)
    - POST /api/point-types/reorder/ - Reorder point types
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PointTypeSerializer
    pagination_class = None  # Disable pagination - users need to see all their types

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePointTypeSerializer
        elif self.action == 'reorder':
            return PointTypeReorderSerializer
        return PointTypeSerializer

    def get_queryset(self):
        """
        Return point types accessible to current user.

        Includes:
        - User's own types (active only)
        - Base types (user=None)

        Ordered by user's custom order if available, otherwise by default order.
        """
        from django.db.models import OuterRef, Subquery, IntegerField, F
        from django.db.models.functions import Coalesce
        from .models import UserTypeOrder

        user = self.request.user

        # Subquery to get user's custom order (avoids JOIN that creates duplicates)
        user_order_subquery = UserTypeOrder.objects.filter(
            user=user,
            type=OuterRef('pk')
        ).values('order')[:1]

        # Get user's types and base types, exclude deleted
        queryset = PointType.objects.filter(
            Q(user=user) | Q(user__isnull=True),
            status='active'
        ).annotate(
            # Get user's custom order if exists, otherwise use type's default order
            custom_order=Coalesce(
                Subquery(user_order_subquery, output_field=IntegerField()),
                F('order'),
                output_field=IntegerField()
            )
        ).order_by('custom_order', 'name')

        return queryset

    def create(self, request):
        """Create new point type for the authenticated user."""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        point_type = serializer.save()

        # Return full serialization
        response_serializer = PointTypeSerializer(point_type, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """Get point type detail."""
        try:
            point_type = PointType.objects.get(pk=pk, status='active')
        except PointType.DoesNotExist:
            raise NotFound('Point type not found')

        # Check permission: user must own the type or it's a base type
        if point_type.user is not None and point_type.user != request.user:
            raise PermissionDenied('You do not have permission to view this type')

        serializer = PointTypeSerializer(point_type, context={'request': request})
        return Response(serializer.data)

    def partial_update(self, request, pk=None):
        """Update point type (partial update only)."""
        try:
            point_type = PointType.objects.get(pk=pk, status='active')
        except PointType.DoesNotExist:
            raise NotFound('Point type not found')

        # Check permission: user must own the type
        if point_type.user != request.user:
            raise PermissionDenied('You can only update your own types')

        serializer = PointTypeSerializer(
            point_type,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        Delete point type (soft delete).

        Switches all associated points to the default 'Point' type.
        """
        try:
            point_type = PointType.objects.get(pk=pk, status='active')
        except PointType.DoesNotExist:
            raise NotFound('Point type not found')

        # Check permission: user must own the type
        if point_type.user != request.user:
            raise PermissionDenied('You can only delete your own types')

        # Get or create default type
        default_type, _ = PointType.objects.get_or_create(
            name='Point',
            user=None,
            defaults={'icon': '📍', 'order': 0}
        )

        # Switch all points with this type to default
        GPSPoint.objects.filter(type=point_type).update(type=default_type)

        # Soft delete the type
        point_type.status = 'deleted'
        point_type.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """
        Reorder point types.

        Expects: {"order": [{"id": "uuid", "order": 1}, ...]}
        """
        serializer = PointTypeReorderSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='upload-icon')
    def upload_icon(self, request):
        """
        Upload an icon file or fetch from URL.

        Accepts either:
        - multipart/form-data with 'file' field (file upload)
        - JSON with 'url' field (download from URL)

        Returns: {"icon_url": "http://localhost:8000/media/point_type_icons/..."}
        """
        allowed_extensions = ['.svg', '.png', '.jpg', '.jpeg']
        max_size = 1 * 1024 * 1024  # 1MB

        # Check if this is a URL download request
        if 'url' in request.data and request.data['url']:
            external_url = request.data['url']

            try:
                # Download the file from the URL
                response = requests.get(external_url, timeout=10, stream=True)
                response.raise_for_status()

                # Check content type
                content_type = response.headers.get('content-type', '')
                if not any(ct in content_type.lower() for ct in ['image/svg', 'image/png', 'image/jpeg', 'image/jpg']):
                    raise ValidationError({
                        'url': f'Invalid content type: {content_type}. Must be SVG, PNG, or JPEG.'
                    })

                # Get file extension from content-type or URL
                if 'svg' in content_type:
                    file_ext = '.svg'
                elif 'png' in content_type:
                    file_ext = '.png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    file_ext = '.jpg'
                else:
                    # Try to get from URL
                    file_ext = os.path.splitext(external_url)[1].lower()
                    if file_ext not in allowed_extensions:
                        file_ext = '.svg'  # Default to SVG

                # Read content
                content = BytesIO()
                total_size = 0
                for chunk in response.iter_content(chunk_size=8192):
                    total_size += len(chunk)
                    if total_size > max_size:
                        raise ValidationError({
                            'url': f'File too large. Maximum size is {max_size / 1024 / 1024}MB'
                        })
                    content.write(chunk)

                content.seek(0)

                # Generate unique filename
                unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
                file_path = os.path.join('point_type_icons', unique_filename)

                # Save file
                saved_path = default_storage.save(file_path, ContentFile(content.read()))

            except requests.RequestException as e:
                raise ValidationError({
                    'url': f'Failed to download icon: {str(e)}'
                })

        # Handle file upload
        elif 'file' in request.FILES:
            uploaded_file = request.FILES['file']

            # Validate file type (SVG, PNG, JPG)
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()

            if file_ext not in allowed_extensions:
                raise ValidationError({
                    'file': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
                })

            # Validate file size (max 1MB)
            if uploaded_file.size > max_size:
                raise ValidationError({
                    'file': f'File too large. Maximum size is {max_size / 1024 / 1024}MB'
                })

            # Generate unique filename
            unique_filename = f"{uuid_lib.uuid4()}{file_ext}"
            file_path = os.path.join('point_type_icons', unique_filename)

            # Save file
            saved_path = default_storage.save(file_path, uploaded_file)

        else:
            raise ValidationError({'error': 'Either file or url must be provided'})

        # Build full URL with request host
        request_host = request.build_absolute_uri('/').rstrip('/')
        media_url = settings.MEDIA_URL.lstrip('/')
        icon_url = f"{request_host}/{media_url}{saved_path}"

        return Response({
            'icon_url': icon_url
        }, status=status.HTTP_201_CREATED)
