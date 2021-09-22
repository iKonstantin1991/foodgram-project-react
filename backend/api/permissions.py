from rest_framework.permissions import SAFE_METHODS, IsAuthenticatedOrReadOnly


class OwnerOrAdminOrAuthenticatedOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in SAFE_METHODS
            or obj.author == request.user
            or request.user.is_staff
        )
