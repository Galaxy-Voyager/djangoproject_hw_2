from rest_framework import viewsets

from .models import User
from .serializers import UserDetailSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        """Используем расширенный сериализатор для детального просмотра"""
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer
