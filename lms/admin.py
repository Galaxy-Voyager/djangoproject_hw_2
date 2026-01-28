from django.contrib import admin

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "preview")
    list_filter = ("title",)
    search_fields = ("title", "description")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "video_link")
    list_filter = ("course",)
    search_fields = ("title", "description", "video_link")
