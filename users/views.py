from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from users.permissions import IsOwner
from .models import User
from .serializers import UserSerializer, UserDetailSerializer, RegisterSerializer


@extend_schema(
    summary="Регистрация пользователя",
    description="Регистрация нового пользователя в системе. "
               "Валидирует пароль и проверяет совпадение паролей."
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        return user


from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes


@extend_schema_view(
    list=extend_schema(
        summary="Список пользователей",
        description="Получение списка всех пользователей (требуется аутентификация)"
    ),
    retrieve=extend_schema(
        summary="Детали пользователя",
        description="Получение детальной информации о пользователе. "
                   "Только владелец профиля видит историю платежей."
    ),
    create=extend_schema(
        summary="Создание пользователя",
        description="Создание нового пользователя. Не требует аутентификации."
    ),
    update=extend_schema(
        summary="Обновление пользователя",
        description="Полное обновление пользователя. Доступно только владельцу профиля."
    ),
    partial_update=extend_schema(
        summary="Частичное обновление пользователя",
        description="Частичное обновление пользователя. Доступно только владельцу профиля."
    ),
    destroy=extend_schema(
        summary="Удаление пользователя",
        description="Удаление пользователя. Доступно только владельцу профиля."
    )
)
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
