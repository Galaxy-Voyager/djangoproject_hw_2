from rest_framework import filters, viewsets

from .models import Payment
from .serializers import PaymentSerializer


from rest_framework import filters, viewsets
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
from .models import Payment
from .serializers import PaymentSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Список платежей",
        description="Получение списка платежей с возможностью фильтрации и сортировки",
        parameters=[
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Сортировка по полю (например: payment_date, -payment_date)'
            ),
            OpenApiParameter(
                name='course',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Фильтр по ID курса'
            ),
            OpenApiParameter(
                name='lesson',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Фильтр по ID урока'
            ),
            OpenApiParameter(
                name='payment_method',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по способу оплаты (cash или transfer)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary="Детали платежа",
        description="Получение детальной информации о платеже"
    ),
    create=extend_schema(
        summary="Создание платежа",
        description="Создание нового платежа"
    ),
    update=extend_schema(
        summary="Обновление платежа",
        description="Полное обновление платежа"
    ),
    partial_update=extend_schema(
        summary="Частичное обновление платежа",
        description="Частичное обновление платежа"
    ),
    destroy=extend_schema(
        summary="Удаление платежа",
        description="Удаление платежа"
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().select_related("user", "course", "lesson")
    serializer_class = PaymentSerializer

    # Простая фильтрация через OrderingFilter
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["payment_date"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        """Ручная фильтрация по query parameters"""
        queryset = super().get_queryset()

        # Фильтрация по курсу
        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        # Фильтрация по уроку
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)

        # Фильтрация по способу оплаты
        payment_method = self.request.query_params.get("payment_method")
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)

        return queryset
