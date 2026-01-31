from django.shortcuts import get_object_or_404
from rest_framework import generics, viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from users.permissions import IsModerator, IsOwner
from .models import Course, Lesson, Subscription
from .serializers import CourseListSerializer, CourseDetailSerializer, LessonSerializer, SubscriptionSerializer
from .paginators import CoursePagination, LessonPagination


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('id')
    permission_classes = [IsAuthenticated]
    pagination_class = CoursePagination

    def get_serializer_class(self):
        """Используем разные сериализаторы для списка и деталей"""
        if self.action == 'list':
            return CourseListSerializer
        elif self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseDetailSerializer

    def check_moderator_permission(self, request):
        """Проверка, является ли пользователь модератором"""
        return request.user.groups.filter(name='moderators').exists()

    def check_owner_permission(self, obj, request):
        """Проверка, является ли пользователь владельцем"""
        return obj.owner == request.user

    def perform_create(self, serializer):
        """При создании курса привязываем его к текущему пользователю"""
        if self.check_moderator_permission(self.request):
            raise PermissionDenied("Модераторы не могут создавать курсы")
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        """При удалении курса проверяем права"""
        if self.check_moderator_permission(self.request):
            raise PermissionDenied("Модераторы не могут удалять курсы")
        if not self.check_owner_permission(instance, self.request):
            raise PermissionDenied("Вы не являетесь владельцем этого курса")
        instance.delete()

    def perform_update(self, serializer):
        """При обновлении курса проверяем права"""
        instance = self.get_object()
        if not (self.check_moderator_permission(self.request) or
                self.check_owner_permission(instance, self.request)):
            raise PermissionDenied("Вы не можете редактировать этот курс")
        serializer.save()

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all().order_by('id')
        return Course.objects.filter(owner=user).order_by('id')


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LessonPagination

    def check_moderator_permission(self, request):
        """Проверка, является ли пользователь модератором"""
        return request.user.groups.filter(name='moderators').exists()

    def check_owner_permission(self, obj, request):
        """Проверка, является ли пользователь владельцем"""
        return obj.owner == request.user

    def perform_create(self, serializer):
        """При создании урока привязываем его к текущему пользователю"""
        if self.check_moderator_permission(self.request):
            raise PermissionDenied("Модераторы не могут создавать уроки")
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all().order_by('id')
        return Lesson.objects.filter(owner=user).order_by('id')


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def check_moderator_permission(self, request):
        """Проверка, является ли пользователь модератором"""
        return request.user.groups.filter(name='moderators').exists()

    def check_owner_permission(self, obj, request):
        """Проверка, является ли пользователь владельцем"""
        return obj.owner == request.user

    def perform_update(self, serializer):
        """При обновлении урока проверяем права"""
        instance = self.get_object()
        if not (self.check_moderator_permission(self.request) or
                self.check_owner_permission(instance, self.request)):
            raise PermissionDenied("Вы не можете редактировать этот урок")
        serializer.save()

    def perform_destroy(self, instance):
        if self.check_moderator_permission(self.request):
            raise PermissionDenied("Модераторы не могут удалять уроки")
        if not self.check_owner_permission(instance, self.request):
            raise PermissionDenied("Вы не являетесь владельцем этого урока")
        instance.delete()

    def get_queryset(self):
        """Фильтруем queryset в зависимости от прав пользователя"""
        user = self.request.user
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all().order_by('id')
        return Lesson.objects.filter(owner=user).order_by('id')


class SubscriptionAPIView(APIView):
    """API для управления подписками на курсы"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем объект курса
        course_item = get_object_or_404(Course, id=course_id)

        # Проверяем существующую подписку
        subs_item = Subscription.objects.filter(user=user, course=course_item)

        # Если подписка существует - удаляем ее
        if subs_item.exists():
            subs_item.delete()
            message = 'Подписка удалена'
        # Если подписки нет - создаем ее
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = 'Подписка добавлена'

        # Возвращаем ответ
        return Response({"message": message}, status=status.HTTP_200_OK)

    def get(self, request):
        """Получение списка подписок пользователя"""
        subscriptions = Subscription.objects.filter(user=request.user)
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)
