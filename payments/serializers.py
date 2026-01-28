from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    course_title = serializers.CharField(
        source="course.title", read_only=True, allow_null=True
    )
    lesson_title = serializers.CharField(
        source="lesson.title", read_only=True, allow_null=True
    )
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "user_email",
            "payment_date",
            "course",
            "course_title",
            "lesson",
            "lesson_title",
            "amount",
            "payment_method",
            "payment_method_display",
        ]
        read_only_fields = ["id", "payment_date"]

    def to_representation(self, instance):
        """Добавляем human-readable отображение способа оплаты"""
        representation = super().to_representation(instance)
        representation["payment_method_display"] = instance.get_payment_method_display()
        return representation
