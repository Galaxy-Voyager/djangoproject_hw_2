import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class StripeService:
    """Сервис для работы с Stripe API"""

    def __init__(self):
        # Установите ваш секретный ключ Stripe
        # Для тестового режима используйте ключ начинающийся с sk_test_
        self.stripe_api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        self.stripe_webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        if not self.stripe_api_key:
            logger.warning("STRIPE_SECRET_KEY не установлен в настройках")

        stripe.api_key = self.stripe_api_key

    def create_product(self, name, description=None):
        """
        Создание продукта в Stripe
        https://stripe.com/docs/api/products/create
        """
        try:
            product = stripe.Product.create(
                name=name,
                description=description,
                metadata={
                    "source": "lms_platform"
                }
            )
            return product
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания продукта в Stripe: {e}")
            raise ValidationError(f"Ошибка создания продукта: {str(e)}")

    def create_price(self, product_id, amount, currency="rub"):
        """
        Создание цены в Stripe
        https://stripe.com/docs/api/prices/create

        Важно: amount передается в копейках (для RUB)
        """
        try:
            # Конвертируем сумму в копейки
            amount_in_cents = int(float(amount) * 100)

            price = stripe.Price.create(
                unit_amount=amount_in_cents,
                currency=currency,
                product=product_id,
                metadata={
                    "source": "lms_platform"
                }
            )
            return price
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания цены в Stripe: {e}")
            raise ValidationError(f"Ошибка создания цены: {str(e)}")
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка конвертации суммы: {e}")
            raise ValidationError(f"Некорректная сумма: {str(e)}")

    def create_checkout_session(self, price_id, success_url, cancel_url, metadata=None):
        """
        Создание сессии для оплаты
        https://stripe.com/docs/api/checkout/sessions/create
        """
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': price_id,
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания сессии в Stripe: {e}")
            raise ValidationError(f"Ошибка создания сессии оплаты: {str(e)}")

    def retrieve_session(self, session_id):
        """
        Получение информации о сессии
        https://stripe.com/docs/api/checkout/sessions/retrieve
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка получения сессии из Stripe: {e}")
            raise ValidationError(f"Ошибка получения информации о сессии: {str(e)}")

    def create_payment_for_course(self, course, user, amount, success_url, cancel_url):
        """
        Полный процесс создания платежа для курса
        """
        try:
            # 1. Создаем продукт
            product = self.create_product(
                name=course.title,
                description=course.description[:500] if course.description else f"Курс: {course.title}"
            )

            # 2. Создаем цену
            price = self.create_price(
                product_id=product.id,
                amount=amount
            )

            # 3. Создаем сессию оплаты
            metadata = {
                "course_id": str(course.id),
                "user_id": str(user.id),
                "type": "course_payment"
            }

            session = self.create_checkout_session(
                price_id=price.id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )

            return {
                "product_id": product.id,
                "price_id": price.id,
                "session_id": session.id,
                "payment_url": session.url,
                "payment_intent_id": session.payment_intent
            }

        except Exception as e:
            logger.error(f"Ошибка создания платежа для курса: {e}")
            raise

    def create_payment_for_lesson(self, lesson, user, amount, success_url, cancel_url):
        """
        Полный процесс создания платежа для урока
        """
        try:
            # 1. Создаем продукт
            product = self.create_product(
                name=lesson.title,
                description=lesson.description[:500] if lesson.description else f"Урок: {lesson.title}"
            )

            # 2. Создаем цену
            price = self.create_price(
                product_id=product.id,
                amount=amount
            )

            # 3. Создаем сессию оплаты
            metadata = {
                "lesson_id": str(lesson.id),
                "user_id": str(user.id),
                "type": "lesson_payment"
            }

            session = self.create_checkout_session(
                price_id=price.id,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata
            )

            return {
                "product_id": product.id,
                "price_id": price.id,
                "session_id": session.id,
                "payment_url": session.url,
                "payment_intent_id": session.payment_intent
            }

        except Exception as e:
            logger.error(f"Ошибка создания платежа для урока: {e}")
            raise

    def check_payment_status(self, session_id):
        """
        Проверка статуса платежа
        """
        try:
            session = self.retrieve_session(session_id)
            return {
                "status": session.payment_status,
                "amount_total": session.amount_total,
                "currency": session.currency,
                "customer_email": session.customer_details.get('email') if session.customer_details else None,
                "payment_intent_id": session.payment_intent
            }
        except Exception as e:
            logger.error(f"Ошибка проверки статуса платежа: {e}")
            raise


# Создаем экземпляр сервиса для использования
stripe_service = StripeService()
