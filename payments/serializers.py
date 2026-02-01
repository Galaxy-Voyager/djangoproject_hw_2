from rest_framework import serializers
from .models import Payment
from .services import stripe_service


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
    stripe_payment_status_display = serializers.SerializerMethodField()
    payment_url = serializers.SerializerMethodField()

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
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "stripe_payment_url",
            "stripe_payment_status",
            "stripe_payment_status_display",
            "stripe_payment_intent_id",
            "payment_url",
        ]
        read_only_fields = [
            "id",
            "payment_date",
            "stripe_product_id",
            "stripe_price_id",
            "stripe_session_id",
            "stripe_payment_url",
            "stripe_payment_status",
            "stripe_payment_intent_id",
        ]

    def get_stripe_payment_status_display(self, obj):
        """Получение человекочитаемого статуса платежа Stripe"""
        if obj.stripe_payment_status:
            status_map = {
                'pending': 'Ожидает оплаты',
                'paid': 'Оплачено',
                'failed': 'Ошибка оплаты',
                'canceled': 'Отменено',
            }
            return status_map.get(obj.stripe_payment_status, obj.stripe_payment_status)
        return None

    def get_payment_url(self, obj):
        """Получение ссылки на оплату для платежей через Stripe"""
        if obj.payment_method == 'stripe' and obj.stripe_payment_url:
            return obj.stripe_payment_url
        return None

    def to_representation(self, instance):
        """Добавляем human-readable отображение способа оплаты"""
        representation = super().to_representation(instance)
        representation["payment_method_display"] = instance.get_payment_method_display()
        return representation

    def validate(self, attrs):
        """Валидация данных платежа"""
        course = attrs.get('course')
        lesson = attrs.get('lesson')

        if course and lesson:
            raise serializers.ValidationError(
                "Можно указать либо курс, либо урок, но не оба одновременно."
            )
        if not course and not lesson:
            raise serializers.ValidationError("Необходимо указать либо курс, либо урок.")
        payment_method = attrs.get('payment_method')
        amount = attrs.get('amount')

        if payment_method == 'stripe':
            if not amount or amount <= 0:
                raise serializers.ValidationError(
                    "Для платежей через Stripe сумма должна быть больше 0."
                )

        return attrs

    def create(self, validated_data):
        """Создание платежа с интеграцией Stripe"""
        request = self.context.get('request')
        user = request.user if request else None
        if validated_data.get('payment_method') == 'stripe':
            course = validated_data.get('course')
            lesson = validated_data.get('lesson')
            amount = validated_data.get('amount')

            if not user:
                raise serializers.ValidationError("Пользователь не авторизован")

            try:
                payment = Payment.objects.create(**validated_data)
                base_url = request.build_absolute_uri('/') if request else 'http://localhost:8000/'
                success_url = f"{base_url}api/payments/success/"
                cancel_url = f"{base_url}api/payments/cancel/"

                if course:
                    stripe_data = stripe_service.create_payment_for_course(
                        course=course,
                        user=user,
                        amount=amount,
                        success_url=success_url,
                        cancel_url=cancel_url
                    )
                elif lesson:
                    stripe_data = stripe_service.create_payment_for_lesson(
                        lesson=lesson,
                        user=user,
                        amount=amount,
                        success_url=success_url,
                        cancel_url=cancel_url
                    )
                payment.stripe_product_id = stripe_data.get('product_id')
                payment.stripe_price_id = stripe_data.get('price_id')
                payment.stripe_session_id = stripe_data.get('session_id')
                payment.stripe_payment_url = stripe_data.get('payment_url')
                payment.stripe_payment_intent_id = stripe_data.get('payment_intent_id')
                payment.save()

                return payment

            except Exception as e:
                if 'payment' in locals():
                    payment.delete()
                raise serializers.ValidationError(f"Ошибка создания платежа в Stripe: {str(e)}")
        return super().create(validated_data)
