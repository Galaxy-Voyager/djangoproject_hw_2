from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CourseViewSet, LessonListCreateView,
                    LessonRetrieveUpdateDestroyView, SubscriptionAPIView)

app_name = "lms"

router = DefaultRouter()
router.register(r"courses", CourseViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list-create"),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyView.as_view(),
        name="lesson-detail",
    ),
    path("subscriptions/", SubscriptionAPIView.as_view(), name="subscriptions"),
]
