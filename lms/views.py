from rest_framework import generics, viewsets, permissions
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsModerator, IsOwner
from .models import Course, Lesson
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Используем разные сериализаторы для списка и деталей"""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        """Кастомные permissions для разных действий"""
        if self.action in ['create', 'destroy']:
            # Создавать и удалять курсы могут только не-модераторы
            self.permission_classes = [IsAuthenticated & ~IsModerator]
        elif self.action in ['update', 'partial_update']:
            # Обновлять могут модераторы ИЛИ владельцы
            self.permission_classes = [IsAuthenticated & (IsModerator | IsOwner)]
        return super().get_permissions()

    def perform_create(self, serializer):
        """При создании курса привязываем его к текущему пользователю"""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            # Модераторы видят все курсы
            return Course.objects.all()
        # Обычные пользователи видят только свои курсы
        return Course.objects.filter(owner=user)


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Разные permissions для разных методов"""
        if self.request.method == 'POST':
            # Создавать уроки могут только не-модераторы
            return [IsAuthenticated & ~IsModerator()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """При создании урока привязываем его к текущему пользователю"""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            # Модераторы видят все уроки
            return Lesson.objects.all()
        # Обычные пользователи видят только свои уроки
        return Lesson.objects.filter(owner=user)


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Кастомные permissions для разных методов"""
        if self.request.method in ['PUT', 'PATCH']:
            # Обновлять могут модераторы ИЛИ владельцы
            return [IsAuthenticated & (IsModerator() | IsOwner())]
        elif self.request.method == 'DELETE':
            # Удалять могут только владельцы (не модераторы)
            return [IsAuthenticated & ~IsModerator() & IsOwner()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            # Модераторы видят все уроки
            return Lesson.objects.all()
        # Обычные пользователи видят только свои уроки
        return Lesson.objects.filter(owner=user)
