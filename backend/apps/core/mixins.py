"""
Core mixins for Django REST Framework views.

Provides reusable patterns for common operations like permission checking.
"""

from rest_framework.exceptions import NotFound


class PermissionCheckMixin:
    """
    Mixin for consistent permission checking in ViewSets.

    Provides methods to retrieve objects with automatic permission validation,
    returning 404 for both missing objects and unauthorized access (to avoid
    leaking information about private resource existence).
    """

    def get_object_with_permission(self, pk, permission_check="can_view"):
        """
        Get object by PK and check permission, returning 404 for unauthorized access.

        This method provides consistent behavior across all viewsets:
        1. Tries to retrieve the object by primary key
        2. Checks if object is in trash (returns 404 if trashed)
        3. Verifies user has required permission
        4. Returns 404 for both missing and unauthorized access

        Args:
            pk: Primary key of the object to retrieve
            permission_check: Name of permission method to call on PermissionService
                            (e.g., 'can_view', 'can_edit', 'is_owner')

        Returns:
            Model instance if found and user has permission

        Raises:
            NotFound: If object doesn't exist, is trashed, or user lacks permission

        Example:
            class MyViewSet(PermissionCheckMixin, viewsets.ModelViewSet):
                def retrieve(self, request, pk=None):
                    obj = self.get_object_with_permission(pk, 'can_view')
                    serializer = self.get_serializer(obj)
                    return Response(serializer.data)
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

        # Check permission
        # Return 404 instead of 403 to avoid leaking information about private resources
        permission_func = getattr(PermissionService, permission_check)
        if not permission_func(obj, self.request.user):
            raise NotFound(f"{model_name} not found")

        return obj
