"""
Points services.

Handles editing locks, spatial queries, and point management logic.
"""

from datetime import timedelta

from django.contrib.gis.geos import Point as GeoPoint
from django.contrib.gis.measure import D
from django.db.models import Q
from django.utils import timezone

from apps.authentication.models import User

from .models import GPSPoint
from .models import PointType
from .models import Tag


class EditingLockService:
    """Service for managing editing locks on GPS points."""

    LOCK_DURATION_MINUTES = 15

    @staticmethod
    def acquire_lock(point: GPSPoint, user: User) -> bool:
        """
        Acquire editing lock for a point.

        Args:
            point: GPSPoint object
            user: User requesting lock

        Returns:
            bool: True if lock acquired, False if point is locked by someone else
        """
        # Check if point is already locked
        if EditingLockService.is_locked(point):
            # If locked by same user, refresh the lock
            if point.editing_lock_user == user:
                point.editing_lock_acquired_at = timezone.now()
                point.save()
                return True

            # Locked by someone else
            return False

        # Acquire lock
        point.editing_lock_user = user
        point.editing_lock_acquired_at = timezone.now()
        point.save()
        return True

    @staticmethod
    def release_lock(point: GPSPoint, user: User) -> bool:
        """
        Release editing lock for a point.

        Args:
            point: GPSPoint object
            user: User releasing lock

        Returns:
            bool: True if lock released, False if user doesn't hold lock
        """
        if point.editing_lock_user != user:
            return False

        point.editing_lock_user = None
        point.editing_lock_acquired_at = None
        point.save()
        return True

    @staticmethod
    def is_locked(point: GPSPoint) -> bool:
        """
        Check if point is currently locked (and not expired).

        Args:
            point: GPSPoint object

        Returns:
            bool: True if locked and not expired, False otherwise
        """
        if not point.editing_lock_user or not point.editing_lock_acquired_at:
            return False

        # Check if lock has expired (15 minutes)
        expiry = point.editing_lock_acquired_at + timedelta(
            minutes=EditingLockService.LOCK_DURATION_MINUTES
        )

        if timezone.now() > expiry:
            # Lock expired, auto-release
            point.editing_lock_user = None
            point.editing_lock_acquired_at = None
            point.save()
            return False

        return True

    @staticmethod
    def get_lock_info(point: GPSPoint) -> dict | None:
        """
        Get lock information for a point.

        Args:
            point: GPSPoint object

        Returns:
            dict: {
                'locked_by': User,
                'acquired_at': datetime,
                'expires_at': datetime
            } or None if not locked
        """
        if not EditingLockService.is_locked(point):
            return None

        return {
            "locked_by": point.editing_lock_user,
            "acquired_at": point.editing_lock_acquired_at,
            "expires_at": point.editing_lock_acquired_at
            + timedelta(minutes=EditingLockService.LOCK_DURATION_MINUTES),
        }

    @staticmethod
    def refresh_lock(point: GPSPoint, user: User) -> bool:
        """
        Refresh lock expiry time (called on edit operations).

        Args:
            point: GPSPoint object
            user: User refreshing lock

        Returns:
            bool: True if lock refreshed, False if user doesn't hold lock
        """
        if point.editing_lock_user != user:
            return False

        point.editing_lock_acquired_at = timezone.now()
        point.save()
        return True


class PointService:
    """Service for GPS point operations."""

    @staticmethod
    def create_point(
        title: str,
        latitude: float,
        longitude: float,
        owner: User,
        description: str = None,
        tags: list[str] = None,
        is_public: bool = False,
        point_type: PointType = None,
    ) -> GPSPoint:
        """
        Create a new GPS point.

        Args:
            title: Point title
            latitude: Latitude (-90 to 90)
            longitude: Longitude (-180 to 180)
            owner: Point owner
            description: Optional HTML description
            tags: Optional list of tag names
            is_public: Public visibility flag
            point_type: Optional PointType instance

        Returns:
            GPSPoint object
        """
        # Set default type if not provided
        if point_type is None:
            point_type = PointType.get_default_type()

        # Create PostGIS Point
        location = GeoPoint(longitude, latitude, srid=4326)

        # Create point
        point = GPSPoint.objects.create(
            title=title,
            description=description,
            location=location,
            owner=owner,
            is_public=is_public,
            type=point_type,
        )

        # Add tags
        if tags:
            for tag_name in tags:
                tag_name_clean = tag_name.strip()
                # Try to find existing tag (case-insensitive)
                try:
                    tag = Tag.objects.get(name__iexact=tag_name_clean, owner=owner)
                except Tag.DoesNotExist:
                    # Create new tag with lowercase name
                    tag = Tag.objects.create(name=tag_name_clean.lower(), owner=owner)
                point.tags.add(tag)

        return point

    @staticmethod
    def update_point(
        point: GPSPoint,
        user: User,
        title: str = None,
        description: str = None,
        latitude: float = None,
        longitude: float = None,
        tags: list[str] = None,
        is_public: bool = None,
        type_id: PointType = None,
    ) -> GPSPoint:
        """
        Update GPS point fields.

        Args:
            point: GPSPoint to update
            user: User performing update
            title: New title (optional)
            description: New description (optional)
            latitude: New latitude (optional)
            longitude: New longitude (optional)
            tags: New tags list (replaces existing)
            is_public: New public flag (optional)
            type_id: New type (optional, PointType instance)

        Returns:
            Updated GPSPoint object
        """
        # Acquire/refresh lock
        EditingLockService.acquire_lock(point, user)

        # Update fields
        if title is not None:
            point.title = title
        if description is not None:
            point.description = description
        if latitude is not None and longitude is not None:
            point.location = GeoPoint(longitude, latitude, srid=4326)
        if is_public is not None:
            point.is_public = is_public
        if type_id is not None:
            point.type = type_id

        point.save()

        # Update tags
        if tags is not None:
            point.tags.clear()
            for tag_name in tags:
                tag_name_clean = tag_name.strip()
                # Try to find existing tag (case-insensitive)
                try:
                    tag = Tag.objects.get(name__iexact=tag_name_clean, owner=user)
                except Tag.DoesNotExist:
                    # Create new tag with lowercase name
                    tag = Tag.objects.create(name=tag_name_clean.lower(), owner=user)
                point.tags.add(tag)

        return point

    @staticmethod
    def delete_point(point: GPSPoint, user: User) -> None:
        """
        Soft delete point (move to trash).

        Args:
            point: GPSPoint to delete
            user: User performing deletion
        """
        from apps.trash.models import Trash

        # Release editing lock if present
        if point.editing_lock_user:
            point.editing_lock_user = None
            point.editing_lock_acquired_at = None
            point.save(update_fields=["editing_lock_user", "editing_lock_acquired_at"])

        # Create trash entry
        Trash.objects.create(
            gps_point=point,
            deleted_by=user,
        )

        # Deactivate shares
        from apps.sharing.models import Share

        Share.objects.filter(gps_point=point).update(is_active=False)

    @staticmethod
    def search_points_by_bbox(
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        user: User = None,
    ) -> list[GPSPoint]:
        """
        Search points within bounding box.

        Args:
            min_lon: Minimum longitude
            min_lat: Minimum latitude
            max_lon: Maximum longitude
            max_lat: Maximum latitude
            user: Optional user for permission filtering

        Returns:
            QuerySet of GPSPoint objects
        """
        from django.contrib.gis.geos import Polygon

        # Create bounding box polygon
        bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))

        # Base query: points within bbox and not trashed
        query = GPSPoint.objects.filter(location__within=bbox).exclude(trash_entry__isnull=False)

        if user and user.is_authenticated:
            # Show owned, shared, or public points

            query = query.filter(
                Q(owner=user)
                | Q(shares__recipient_user=user, shares__is_active=True)
                | Q(is_public=True)
            ).distinct()
        else:
            # Show only public points
            query = query.filter(is_public=True)

        return query

    @staticmethod
    def search_points_nearby(
        latitude: float,
        longitude: float,
        radius_meters: float,
        user: User = None,
    ) -> list[GPSPoint]:
        """
        Search points within radius of a location.

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_meters: Search radius in meters
            user: Optional user for permission filtering

        Returns:
            QuerySet of GPSPoint objects
        """
        location = GeoPoint(longitude, latitude, srid=4326)

        # Base query: points within radius and not trashed
        query = GPSPoint.objects.filter(
            location__distance_lte=(location, D(m=radius_meters))
        ).exclude(trash_entry__isnull=False)

        if user and user.is_authenticated:
            # Show owned, shared, or public points

            query = query.filter(
                Q(owner=user)
                | Q(shares__recipient_user=user, shares__is_active=True)
                | Q(is_public=True)
            ).distinct()
        else:
            # Show only public points
            query = query.filter(is_public=True)

        return query.order_by("location__distance")

    @staticmethod
    def search_points_by_tags(
        tag_names: list[str],
        user: User = None,
    ) -> list[GPSPoint]:
        """
        Search points by tag names (case-insensitive).

        Args:
            tag_names: List of tag names
            user: Optional user for permission filtering

        Returns:
            QuerySet of GPSPoint objects
        """
        # Build Q objects for case-insensitive tag matching
        tag_queries = Q()
        for tag_name in tag_names:
            tag_queries |= Q(tags__name__iexact=tag_name)

        # Base query: points with any of the tags and not trashed
        query = GPSPoint.objects.filter(tag_queries).exclude(trash_entry__isnull=False)

        if user and user.is_authenticated:
            # Show owned, shared, or public points

            query = query.filter(
                Q(owner=user)
                | Q(shares__recipient_user=user, shares__is_active=True)
                | Q(is_public=True)
            ).distinct()
        else:
            # Show only public points
            query = query.filter(is_public=True)

        return query

    @staticmethod
    def search_points_by_text(
        search_text: str,
        user: User = None,
    ) -> list[GPSPoint]:
        """
        Full-text search in title and description.

        Args:
            search_text: Search query
            user: Optional user for permission filtering

        Returns:
            QuerySet of GPSPoint objects
        """
        # Base query: text search in title/description and not trashed
        query = GPSPoint.objects.filter(
            Q(title__icontains=search_text) | Q(description__icontains=search_text)
        ).exclude(trash_entry__isnull=False)

        if user and user.is_authenticated:
            # Show owned, shared, or public points

            query = query.filter(
                Q(owner=user)
                | Q(shares__recipient_user=user, shares__is_active=True)
                | Q(is_public=True)
            ).distinct()
        else:
            # Show only public points
            query = query.filter(is_public=True)

        return query
