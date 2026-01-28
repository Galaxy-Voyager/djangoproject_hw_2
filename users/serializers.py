from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "city",
            "avatar",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "is_active", "is_staff", "date_joined"]


class UserDetailSerializer(UserSerializer):
    """Расширенный сериализатор с историей платежей"""

    payment_history = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["payment_history"]

    def get_payment_history(self, obj):
        """Получение истории платежей пользователя"""
        from payments.serializers import PaymentSerializer

        payments = obj.payments.all().order_by("-payment_date")[:10]
        return PaymentSerializer(payments, many=True, context=self.context).data
