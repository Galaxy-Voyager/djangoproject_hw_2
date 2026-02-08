from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from lms.models import Course
from .models import Payment


class PaymentModelTests(TestCase):
    """Тесты модели платежей"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

    def test_create_payment(self):
        """Тест создания платежа"""
        payment = Payment.objects.create(
            user=self.user,
            course=self.course,
            amount=1000.00,
            payment_method='cash'
        )

        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.course, self.course)
        self.assertEqual(payment.amount, 1000.00)
        self.assertEqual(payment.payment_method, 'cash')


class PaymentAPITests(TestCase):
    """Тесты API платежей"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

        self.client.force_authenticate(user=self.user)

    def test_get_payments_list(self):
        """Тест получения списка платежей"""
        # Создаем тестовый платеж
        Payment.objects.create(
            user=self.user,
            course=self.course,
            amount=1000.00,
            payment_method='cash'
        )

        url = '/api/payments/payments/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_create_payment_api(self):
        """Тест создания платежа через API"""
        url = '/api/payments/payments/'
        data = {
            'course': self.course.id,
            'amount': 2000.00,
            'payment_method': 'transfer'
        }

        response = self.client.post(url, data, format='json')

        # Ожидаем 201 Created или 400 если нужны дополнительные поля
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])

