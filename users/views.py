from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.permissions import IsOwner
from .models import User
from .serializers import UserSerializer, UserDetailSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        return user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Используем расширенный сериализатор для детального просмотра"""
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        """Разные permissions для разных действий"""
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Редактировать и удалять можно только свой профиль
            return [IsAuthenticated & IsOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Пользователи видят список всех пользователей, но с ограниченными данными"""
        user = self.request.user
        if self.action == 'list':
            # Для списка показываем всех пользователей
            return User.objects.all()
        # Для других действий используем базовый queryset
        return super().get_queryset()
