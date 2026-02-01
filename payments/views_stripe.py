from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .models import Payment
from .services import stripe_service
from .serializers import PaymentSerializer


class StripeCheckoutView(APIView):
    """
    View для создания платежной сессии Stripe
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Создание платежной сессии Stripe",
        description="Создание платежной сессии для оплаты курса или урока через Stripe",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'course_id': {
                        'type': 'integer',
                        'description': 'ID курса для оплаты'
                    },
                    'lesson_id': {
                        'type': 'integer',
                        'description': 'ID урока для оплаты'
                    },
                    'amount': {
                        'type': 'number',
                        'description': 'Сумма оплаты'
                    }
                },
                'required': ['amount']
            }
        },
        responses={
            201: OpenApiResponse(
                description="Платежная сессия создана",
                response=PaymentSerializer
            ),
            400: OpenApiResponse(
                description="Ошибка валидации"
            )
        }
    )
    def post(self, request):
        """
        Создание платежной сессии Stripe для курса или урока
        """
        course_id = request.data.get('course_id')
        lesson_id = request.data.get('lesson_id')
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {"error": "Поле amount обязательно"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if course_id and lesson_id:
            return Response(
                {"error": "Можно указать либо course_id, либо lesson_id, но не оба одновременно"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not course_id and not lesson_id:
            return Response(
                {"error": "Необходимо указать либо course_id, либо lesson_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from lms.models import Course, Lesson

            if course_id:
                course = get_object_or_404(Course, id=course_id)
                payment_data = {
                    'user': request.user,
                    'course': course,
                    'amount': amount,
                    'payment_method': 'stripe',
                }
                base_url = request.build_absolute_uri('/')
                success_url = f"{base_url}api/payments/success/"
                cancel_url = f"{base_url}api/payments/cancel/"
                stripe_data = stripe_service.create_payment_for_course(
                    course=course,
                    user=request.user,
                    amount=amount,
                    success_url=success_url,
                    cancel_url=cancel_url
                )
                payment = Payment.objects.create(
                    **payment_data,
                    stripe_product_id=stripe_data.get('product_id'),
                    stripe_price_id=stripe_data.get('price_id'),
                    stripe_session_id=stripe_data.get('session_id'),
                    stripe_payment_url=stripe_data.get('payment_url'),
                    stripe_payment_intent_id=stripe_data.get('payment_intent_id')
                )

            else:  # lesson_id
                lesson = get_object_or_404(Lesson, id=lesson_id)
                payment_data = {
                    'user': request.user,
                    'lesson': lesson,
                    'amount': amount,
                    'payment_method': 'stripe',
                }
                base_url = request.build_absolute_uri('/')
                success_url = f"{base_url}api/payments/success/"
                cancel_url = f"{base_url}api/payments/cancel/"
                stripe_data = stripe_service.create_payment_for_lesson(
                    lesson=lesson,
                    user=request.user,
                    amount=amount,
                    success_url=success_url,
                    cancel_url=cancel_url
                )
                payment = Payment.objects.create(
                    **payment_data,
                    stripe_product_id=stripe_data.get('product_id'),
                    stripe_price_id=stripe_data.get('price_id'),
                    stripe_session_id=stripe_data.get('session_id'),
                    stripe_payment_url=stripe_data.get('payment_url'),
                    stripe_payment_intent_id=stripe_data.get('payment_intent_id')
                )
            serializer = PaymentSerializer(payment, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StripePaymentStatusView(APIView):
    """
    View для проверки статуса платежа Stripe
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Проверка статуса платежа Stripe",
        description="Получение текущего статуса платежа по ID сессии Stripe",
        parameters=[],
        responses={
            200: OpenApiResponse(
                description="Статус платежа получен",
                examples=[
                    OpenApiExample(
                        'Пример ответа',
                        value={
                            "status": "paid",
                            "amount_total": 100000,
                            "currency": "rub",
                            "customer_email": "user@example.com",
                            "payment_intent_id": "pi_123456789"
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="Платеж не найден"
            )
        }
    )
    def get(self, request, session_id=None):
        """
        Проверка статуса платежа по ID сессии Stripe
        """
        if not session_id:
            payment_id = request.query_params.get('payment_id')
            if payment_id:
                payment = get_object_or_404(Payment, id=payment_id, user=request.user)
                session_id = payment.stripe_session_id
            else:
                return Response(
                    {"error": "Необходимо указать session_id или payment_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            status_data = stripe_service.check_payment_status(session_id)
            try:
                payment = Payment.objects.get(
                    stripe_session_id=session_id,
                    user=request.user
                )
                payment.stripe_payment_status = status_data.get('status')
                payment.save()
            except Payment.DoesNotExist:
                pass

            return Response(status_data)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class StripeWebhookView(APIView):
    """
    View для обработки webhook от Stripe
    (для обработки событий оплаты в реальном времени)
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        summary="Webhook для событий Stripe",
        description="Эндпоинт для получения событий от Stripe о статусе платежей",
        request={},
        responses={
            200: OpenApiResponse(
                description="Webhook успешно обработан"
            )
        },
        exclude=True
    )
    def post(self, request):
        """
        Обработка webhook от Stripe
        """
        import json
        from django.views.decorators.csrf import csrf_exempt
        from django.http import HttpResponse

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_service.stripe_webhook_secret
            )
        except ValueError as e:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            return HttpResponse(status=400)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            try:
                payment = Payment.objects.get(stripe_session_id=session['id'])
                payment.stripe_payment_status = 'paid'
                payment.stripe_payment_intent_id = session.get('payment_intent')
                payment.save()

                # Здесь можно добавить дополнительную логику,
                # например, отправку уведомления пользователю

            except Payment.DoesNotExist:
                pass

        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            try:
                payment = Payment.objects.get(stripe_session_id=session['id'])
                payment.stripe_payment_status = 'canceled'
                payment.save()
            except Payment.DoesNotExist:
                pass

        return HttpResponse(status=200)


class PaymentSuccessView(generics.GenericAPIView):
    """
    View для успешной оплаты (редирект после успешной оплаты)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Страница успешной оплаты",
        description="Страница, на которую пользователь перенаправляется после успешной оплаты",
        responses={
            200: OpenApiResponse(
                description="Оплата успешно завершена"
            )
        },
        exclude=False
    )
    def get(self, request):
        """
        Обработка успешной оплаты
        """
        session_id = request.query_params.get('session_id')
        payment_id = request.query_params.get('payment_id')

        context = {
            "success": True,
            "message": "Оплата успешно завершена!",
            "session_id": session_id,
            "payment_id": payment_id,
        }

        return Response(context)


class PaymentCancelView(generics.GenericAPIView):
    """
    View для отмены оплаты (редирект при отмене оплаты)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Страница отмены оплаты",
        description="Страница, на которую пользователь перенаправляется при отмене оплаты",
        responses={
            200: OpenApiResponse(
                description="Оплата отменена"
            )
        },
        exclude=False
    )
    def get(self, request):
        """
        Обработка отмены оплаты
        """
        session_id = request.query_params.get('session_id')
        payment_id = request.query_params.get('payment_id')

        context = {
            "success": False,
            "message": "Оплата отменена.",
            "session_id": session_id,
            "payment_id": payment_id,
        }

        return Response(context)
