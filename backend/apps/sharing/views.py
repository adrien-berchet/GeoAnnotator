"""
Sharing views for managing point shares and invitations.
"""

from django.db import models
from django.http import Http404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.points.models import GPSPoint

from .models import Friendship
from .models import Share
from .serializers import AcceptShareSerializer
from .serializers import AddFriendSerializer
from .serializers import BatchShareSerializer
from .serializers import CreateShareSerializer
from .serializers import FriendDetailSerializer
from .serializers import FriendSerializer
from .serializers import FriendshipSerializer
from .serializers import ShareSerializer
from .serializers import UpdateShareSerializer
from .services import BatchShareService
from .services import FriendshipService
from .services import PermissionService
from .services import ShareService


class ShareViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Share CRUD operations and invitation management.

    Endpoints:
    - GET /api/points/{point_id}/shares/ - List shares for specific point
    - POST /api/points/{point_id}/shares/ - Create new share (send invitation)
    - GET /api/points/{point_id}/shares/{id}/ - Retrieve share detail
    - PUT /api/points/{point_id}/shares/{id}/ - Update share permission level
    - DELETE /api/points/{point_id}/shares/{id}/ - Revoke share
    - POST /api/shares/accept/{token}/ - Accept invitation by token
    - GET /api/shares/received/ - List received shares
    """

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return CreateShareSerializer
        elif self.action in ["update", "partial_update"]:
            return UpdateShareSerializer
        elif self.action == "accept":
            return AcceptShareSerializer
        return ShareSerializer

    def get_queryset(self):
        """Return shares for points owned by current user, or shares where user is recipient."""
        user = self.request.user

        # If point_id in URL kwargs (nested route), filter by that point
        point_id = self.kwargs.get("point_id")
        if point_id:
            # For listing shares of a specific point, user must be owner
            return Share.objects.filter(
                gps_point_id=point_id, gps_point__owner=user, is_active=True
            ).select_related("gps_point", "owner", "recipient_user")

        # Get shares for owned points OR shares where user is recipient
        return Share.objects.filter(
            models.Q(gps_point__owner=user) | models.Q(recipient_email=user.email)
        ).select_related("gps_point", "owner", "recipient_user")

    def list(self, request, point_id=None):
        """List shares for a point (owner only)."""
        if point_id:
            # Check if user is owner of the point
            try:
                point = GPSPoint.objects.get(id=point_id)
            except GPSPoint.DoesNotExist:
                raise Http404("Point not found") from None

            if point.owner != request.user:
                return Response(
                    {"error": "Permission denied. Only the point owner can list shares."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        queryset = self.get_queryset()
        serializer = ShareSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request, point_id=None):
        """Create new share (send invitation)."""
        # Get point from URL kwargs (nested route)
        try:
            point = GPSPoint.objects.get(id=point_id)
        except GPSPoint.DoesNotExist:
            raise Http404("Point not found") from None

        # Check transfer permission (can share)
        if not PermissionService.can_share(point, request.user):
            return Response(
                {"error": "You do not have permission to share this point"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Pass point in serializer context
        serializer = CreateShareSerializer(
            data=request.data, context={"request": request, "gps_point": point}
        )
        serializer.is_valid(raise_exception=True)

        # Validate permission level
        user_permission = PermissionService.get_user_permission(point, request.user)
        requested_permission = serializer.validated_data["permission_level"]

        # Cannot grant higher permission than you have
        permission_hierarchy = {"view": 1, "edit": 2, "transfer": 3, "owner": 4}
        if permission_hierarchy.get(requested_permission, 0) >= permission_hierarchy.get(
            user_permission, 0
        ):
            return Response(
                {
                    "error": f"Cannot grant {requested_permission} permission (you have {user_permission})"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create share via serializer (handles service call)
            share = serializer.save()

            response_serializer = ShareSerializer(share, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None, point_id=None):
        """Get share detail."""
        share = self.get_object()

        # Check if user has permission to view this share
        if not (
            PermissionService.is_owner(share.gps_point, request.user)
            or share.recipient_email == request.user.email
        ):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = ShareSerializer(share, context={"request": request})
        return Response(serializer.data)

    def update(self, request, pk=None, point_id=None):
        """Update share permission level."""
        return self.partial_update(request, pk, point_id)

    def partial_update(self, request, pk=None, point_id=None):
        """Update share permission level."""
        share = self.get_object()

        # Only point owner or higher-permission user can update shares
        if not PermissionService.can_share(share.gps_point, request.user):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        serializer = UpdateShareSerializer(
            share, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        new_permission = serializer.validated_data.get("permission_level")

        if new_permission:
            try:
                # Update via service
                ShareService.update_share_permission(
                    share=share, permission_level=new_permission, user=request.user
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = ShareSerializer(share, context={"request": request})
        return Response(response_serializer.data)

    def destroy(self, request, pk=None, point_id=None):
        """Revoke share."""
        share = self.get_object()

        # Only point owner or share creator can revoke
        if not (
            PermissionService.is_owner(share.gps_point, request.user) or share.owner == request.user
        ):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Revoke via service (cascade deletes downstream shares)
            ShareService.revoke_share(share, request.user, cascade=True)

            return Response(status=status.HTTP_204_NO_CONTENT)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def received(self, request):
        """List shares received by current user."""
        shares = Share.objects.filter(
            recipient_email=request.user.email, is_active=True
        ).select_related("gps_point", "owner", "recipient_user")

        serializer = ShareSerializer(shares, many=True, context={"request": request})
        return Response(serializer.data)

    def accept(self, request, token=None):
        """Accept invitation by token."""
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Accept invitation via service
            share = ShareService.accept_invitation(str(token), request.user)

            response_serializer = ShareSerializer(share, context={"request": request})
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FriendshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Friendship CRUD operations.

    Endpoints:
    - GET /api/v1/friendships/ - List all friends with share stats
    - POST /api/v1/friendships/ - Add a friend by username
    - GET /api/v1/friendships/{id}/ - Get friend detail with shared points
    - DELETE /api/v1/friendships/{id}/ - Remove friend (revokes all shares)
    """

    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "create":
            return AddFriendSerializer
        elif self.action == "retrieve":
            return FriendDetailSerializer
        elif self.action == "list":
            return FriendSerializer
        return FriendshipSerializer

    def get_queryset(self):
        """Return friendships for current user."""
        user = self.request.user
        return Friendship.objects.filter(user=user).select_related("friend")

    def list(self, request):
        """List all friends with share statistics."""
        user = request.user

        # Get friends with share stats from service
        friends = FriendshipService.get_friends(user)

        serializer = FriendSerializer(
            friends, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def create(self, request):
        """Add a friend by username."""
        serializer = AddFriendSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            friendship = serializer.save()

            # Return the created friendship
            response_serializer = FriendshipSerializer(
                friendship, context={"request": request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """Get friend detail with shared points."""
        try:
            friendship = self.get_object()
            friend = friendship.friend
        except Friendship.DoesNotExist:
            return Response(
                {"error": "Friendship not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get shared points with this friend
        shared_points = FriendshipService.get_shared_points_with_friend(
            request.user, friend
        )

        # Get share counts
        from django.db.models import Count, Q

        shares_sent_count = Share.objects.filter(
            owner=request.user, recipient_user=friend, is_active=True
        ).count()

        shares_received_count = Share.objects.filter(
            owner=friend, recipient_user=request.user, is_active=True
        ).count()

        # Prepare friend detail data - pass queryset, not serialized data
        friend_data = {
            "id": friend.id,
            "username": friend.username,
            "email": friend.email,
            "friendship_created_at": friendship.created_at,
            "shared_points": shared_points,  # Pass queryset, let serializer handle it
            "shares_sent_count": shares_sent_count,
            "shares_received_count": shares_received_count,
        }

        serializer = FriendDetailSerializer(friend_data, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        """
        Remove friend and revoke all shares in both directions.

        Returns count of revoked shares.
        """
        try:
            friendship = self.get_object()
            friend = friendship.friend
        except Friendship.DoesNotExist:
            return Response(
                {"error": "Friendship not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Remove friend via service (handles bidirectional removal and share revocation)
            result = FriendshipService.remove_friend(request.user, friend)

            return Response(
                {
                    "message": f"Successfully removed {friend.username} as friend",
                    "friendships_deleted": result["friendships_deleted"],
                    "shares_revoked": result["total_shares_revoked"],
                    "details": {
                        "shares_revoked_to_friend": result["shares_revoked_to_friend"],
                        "shares_revoked_from_friend": result["shares_revoked_from_friend"],
                    },
                },
                status=status.HTTP_200_OK,
            )

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BatchShareView(viewsets.ViewSet):
    """
    ViewSet for batch sharing operations.

    Endpoints:
    - POST /api/v1/sharing/batch/ - Share multiple points with multiple users
    """

    permission_classes = [IsAuthenticated]

    def create(self, request):
        """
        Batch share multiple points with multiple users.

        Request body:
        {
            "point_ids": ["uuid1", "uuid2", ...],
            "usernames": ["user1", "user2", ...],
            "permission_level": "view" | "edit" | "transfer"
        }

        Response:
        {
            "success_count": int,
            "error_count": int,
            "total_attempted": int,
            "results": [...]
        }
        """
        serializer = BatchShareSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        result = serializer.save()

        # Return appropriate status code based on results
        if result["error_count"] == 0:
            return Response(result, status=status.HTTP_201_CREATED)
        elif result["success_count"] == 0:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Partial success
            return Response(result, status=status.HTTP_207_MULTI_STATUS)
