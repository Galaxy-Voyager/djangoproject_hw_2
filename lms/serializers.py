from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import YouTubeURLValidator


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"
        validators = [
            YouTubeURLValidator(field='video_link'),
        ]

    def validate_video_link(self, value):
        """Валидация поля video_link"""
        if value:
            from .validators import validate_youtube_url
            return validate_youtube_url(value)
        return value


class CourseLessonSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для отображения уроков в курсе"""

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'preview', 'video_link']


class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка курсов (только основные данные)"""
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons_count', 'is_subscribed']

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяем, подписан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False


class CourseDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра курса (со всеми уроками)"""
    lessons = CourseLessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяем, подписан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""
    user_email = serializers.CharField(source="user.email", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "user", "user_email", "course", "course_title", "subscribed_at"]
        read_only_fields = ["id", "subscribed_at"]


class CourseSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подписки в курсе"""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'is_subscribed']

    def get_is_subscribed(self, obj):
        """Проверяем, подписан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False
