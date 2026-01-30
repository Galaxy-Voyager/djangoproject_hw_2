from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = "__all__"


class CourseLessonSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для отображения уроков в курсе"""

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'preview', 'video_link']


class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка курсов (только основные данные)"""
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons_count']

    def get_lessons_count(self, obj):
        return obj.lessons.count()


class CourseDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра курса (со всеми уроками)"""
    lessons = CourseLessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_lessons_count(self, obj):
        return obj.lessons.count()
