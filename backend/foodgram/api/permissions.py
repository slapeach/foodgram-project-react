from rest_framework import permissions
from users.models import ADMIN


class IsAdminOrReadOnly(permissions.BasePermission):
    """Пермишен для Админа, или только чтение"""
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user
            and request.user.is_authenticated
            and (request.user.role == ADMIN)
        )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """Пермишен для автора, админа и модератора, или только чтение"""
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user
            and request.user.is_authenticated
            and (request.user == obj.author
                 or (request.user.role == ADMIN))
        )
