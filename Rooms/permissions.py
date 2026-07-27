from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permissions(self, request):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff