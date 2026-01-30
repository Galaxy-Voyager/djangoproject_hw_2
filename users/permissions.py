from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    """Проверка, является ли пользователь модератором"""

    def has_permission(self, request, view):
        return request.user.groups.filter(name='moderators').exists()


class IsOwner(permissions.BasePermission):
    """Проверка, является ли пользователь владельцем объекта"""

    def has_object_permission(self, request, view, obj):
        # Проверяем, есть ли у объекта поле 'owner'
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        # Или проверяем поле 'user' для платежей
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        # Для модели User сравниваем сам объект с request.user
        elif obj.__class__.__name__ == 'User':
            return obj == request.user
        return False
