"""
Core mixins for Django REST Framework views.

Provides reusable patterns for common operations like permission checking.
"""

from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied


class PermissionCheckMixin:
    """
    Mixin for consistent permission checking in ViewSets.

    Provides methods to retrieve objects with automatic permission validation,
    returning 404 for both missing objects and unauthorized access (to avoid
    leaking information about private resource existence).
    """

    def get_object_with_permission(self, pk, permission_check="can_view"):
        """
        Get object by PK and check permission with smart 404/403 error handling.

        This method provides consistent behavior across all viewsets:
        1. Tries to retrieve the object by primary key
        2. Checks if object is in trash (returns 404 if trashed)
        3. Verifies user can VIEW the resource (404 if not, to avoid leaking existence)
        4. For write operations, verifies specific permission (403 if user can view but not write)

        Security logic:
        - If user can't view the resource → 404 (never reveal existence of private resources)
        - If user can view but lacks write permission → 403 (user knows it exists)

        Args:
            pk: Primary key of the object to retrieve
            permission_check: Name of permission method to call on PermissionService
                            (e.g., 'can_view', 'can_edit', 'is_owner', 'can_share')

        Returns:
            Model instance if found and user has permission

        Raises:
            NotFound: If object doesn't exist, is trashed, or user can't view it
            PermissionDenied: If user can view but lacks the requested write permission

        Example:
            class MyViewSet(PermissionCheckMixin, viewsets.ModelViewSet):
                def retrieve(self, request, pk=None):
                    obj = self.get_object_with_permission(pk, 'can_view')
                    return Response(self.get_serializer(obj).data)

                def update(self, request, pk=None):
                    obj = self.get_object_with_permission(pk, 'can_edit')
                    # Can view but not edit → 403
                    # Can't view at all → 404
        """
        from apps.sharing.services import PermissionService

        # Get the model class from the viewset's queryset
        model_class = self.get_queryset().model
        model_name = model_class.__name__

        # Try to retrieve the object
        try:
            obj = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            raise NotFound(f"{model_name} not found") from None

        # Check if object is in trash (soft-deleted)
        if hasattr(obj, "trash_entry") and obj.trash_entry:
            raise NotFound(f"{model_name} not found")

        # First check if user can even VIEW the resource
        if not PermissionService.can_view(obj, self.request.user):
            # User can't see the resource → 404 (don't leak existence)
            raise NotFound(f"{model_name} not found")

        # If requesting view permission, we're done (user has it)
        if permission_check == "can_view":
            return obj

        # For write operations, check the specific permission
        permission_func = getattr(PermissionService, permission_check)
        if not permission_func(obj, self.request.user):
            # User can VIEW but can't perform the write operation → 403
            raise PermissionDenied("You do not have permission to perform this action.")

        return obj
