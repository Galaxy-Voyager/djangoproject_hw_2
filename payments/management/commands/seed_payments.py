from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from lms.models import Course, Lesson
from payments.models import Payment
from users.models import User


class Command(BaseCommand):
    help = "Создание тестовых данных для платежей"

    def handle(self, *args, **kwargs):
        # Получаем существующих пользователей
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.ERROR("Сначала создайте пользователей!"))
            return

        # Получаем существующие курсы и уроки
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not courses.exists() or not lessons.exists():
            self.stdout.write(self.style.ERROR("Сначала создайте курсы и уроки!"))
            return

        # Создаем тестовые платежи
        payments_data = [
            {
                "user": users[0],
                "course": courses[0],
                "lesson": None,
                "amount": Decimal("10000.00"),
                "payment_method": "transfer",
                "payment_date": timezone.datetime(2024, 1, 15, 10, 30, 0),
            },
            {
                "user": users[0],
                "course": None,
                "lesson": lessons[0],
                "amount": Decimal("1500.00"),
                "payment_method": "cash",
                "payment_date": timezone.datetime(2024, 1, 20, 14, 45, 0),
            },
            {
                "user": users[1] if len(users) > 1 else users[0],
                "course": courses[1] if len(courses) > 1 else courses[0],
                "lesson": None,
                "amount": Decimal("12000.00"),
                "payment_method": "transfer",
                "payment_date": timezone.datetime(2024, 1, 25, 9, 15, 0),
            },
            {
                "user": users[1] if len(users) > 1 else users[0],
                "course": None,
                "lesson": lessons[1] if len(lessons) > 1 else lessons[0],
                "amount": Decimal("2000.00"),
                "payment_method": "cash",
                "payment_date": timezone.datetime(2024, 2, 1, 16, 20, 0),
            },
        ]

        created_count = 0
        for payment_data in payments_data:
            payment, created = Payment.objects.get_or_create(
                user=payment_data["user"],
                payment_date=payment_data["payment_date"],
                defaults={
                    "course": payment_data["course"],
                    "lesson": payment_data["lesson"],
                    "amount": payment_data["amount"],
                    "payment_method": payment_data["payment_method"],
                },
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Успешно создано {created_count} платежей")
        )
