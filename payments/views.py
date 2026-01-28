from rest_framework import filters, viewsets

from .models import Payment
from .serializers import PaymentSerializer


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
