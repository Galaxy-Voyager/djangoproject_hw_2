import os
import django
import time
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from lms.tasks import send_course_update_notification, check_course_updates_and_notify
from users.tasks import check_inactive_users, send_block_notification
from lms.models import Course, Subscription
from users.models import User
from django.utils import timezone
from datetime import timedelta


def print_header(text):
    """Красивый заголовок"""
    print("\n" + "=" * 80)
    print(f"📋 {text}")
    print("=" * 80)


def print_success(text):
    """Успешное сообщение"""
    print(f"\n✅ {text}")


def print_error(text):
    """Сообщение об ошибке"""
    print(f"\n❌ {text}")


def wait_for_task(task, task_name="Задача", max_wait=10):
    """Ожидание выполнения задачи"""
    print(f"⏳ Ожидание выполнения {task_name} (ID: {task.id})...")

    for i in range(max_wait):
        if task.ready():
            result = task.result
            print_success(f"{task_name} выполнена за {i + 1} секунд")
            print(f"   Результат: {result}")
            return True, result
        time.sleep(1)

    print_error(f"{task_name} не завершилась за {max_wait} секунд")
    return False, None


def setup_test_environment():
    """Настройка тестового окружения"""
    print_header("НАСТРОЙКА ТЕСТОВОГО ОКРУЖЕНИЯ")

    # Очищаем старые тестовые данные
    User.objects.filter(email__contains='test_').delete()
    Course.objects.filter(title__contains='Тестовый').delete()

    # Создаем уникальный ID для теста
    test_id = random.randint(100000, 999999)
    print(f"🆔 Тестовый ID: {test_id}")

    return test_id


def create_test_users(test_id):
    """Создание тестовых пользователей"""
    print_header("СОЗДАНИЕ ТЕСТОВЫХ ПОЛЬЗОВАТЕЛЕЙ")

    users = []

    # Пользователь 1 - владелец курса
    user1 = User.objects.create_user(
        email=f'test_owner_{test_id}@example.com',
        password='testpass123',
        first_name='Владелец',
        last_name='Курса'
    )
    users.append(user1)
    print(f"👤 Создан владелец: {user1.email}")

    # Пользователь 2 - подписчик
    user2 = User.objects.create_user(
        email=f'test_subscriber_{test_id}@example.com',
        password='testpass123',
        first_name='Подписчик',
        last_name='Тестовый'
    )
    users.append(user2)
    print(f"👤 Создан подписчик: {user2.email}")

    # Пользователь 3 - неактивный
    user3 = User.objects.create_user(
        email=f'test_inactive_{test_id}@example.com',
        password='testpass123',
        first_name='Неактивный',
        last_name='Пользователь'
    )
    user3.last_login = timezone.now() - timedelta(days=35)
    user3.save()
    users.append(user3)
    print(f"👤 Создан неактивный пользователь: {user3.email}")
    print(f"   Последний вход: {user3.last_login.date()}")

    return users


def create_test_course(owner, test_id):
    """Создание тестового курса"""
    print_header("СОЗДАНИЕ ТЕСТОВОГО КУРСА")

    course = Course.objects.create(
        title=f'Тестовый курс Celery {test_id}',
        description='Это тестовый курс для проверки работы Celery задач и уведомлений.',
        owner=owner
    )

    print(f"📚 Создан курс: '{course.title}'")
    print(f"   Владелец: {owner.email}")
    print(f"   ID курса: {course.id}")

    return course


def setup_subscriptions(course, subscribers):
    """Настройка подписок"""
    print_header("НАСТРОЙКА ПОДПИСОК")

    for subscriber in subscribers:
        Subscription.objects.create(user=subscriber, course=course)
        print(f"📌 Подписка: {subscriber.email} -> {course.title}")

    subscription_count = Subscription.objects.filter(course=course).count()
    print_success(f"Создано подписок: {subscription_count}")


def test_course_notification(course):
    """Тест отправки уведомлений о курсе"""
    print_header("ТЕСТ: ОТПРАВКА УВЕДОМЛЕНИЙ О КУРСЕ")

    print(f"🎯 Тестируем отправку уведомлений для курса:")
    print(f"   Название: {course.title}")
    print(f"   ID: {course.id}")

    # Запускаем задачу
    task = send_course_update_notification.delay(course.id)

    # Ждем выполнения
    success, result = wait_for_task(task, "Отправка уведомлений о курсе")

    return success


def test_block_notification(user):
    """Тест отправки уведомления о блокировке"""
    print_header("ТЕСТ: ОТПРАВКА УВЕДОМЛЕНИЯ О БЛОКИРОВКЕ")

    print(f"🎯 Тестируем отправку уведомления о блокировке:")
    print(f"   Пользователь: {user.email}")
    print(f"   ID: {user.id}")

    # Запускаем задачу
    task = send_block_notification.delay(user.id)

    # Ждем выполнения
    success, result = wait_for_task(task, "Уведомление о блокировке")

    return success


def test_inactive_users_check():
    """Тест проверки неактивных пользователей"""
    print_header("ТЕСТ: ПРОВЕРКА НЕАКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ")

    print("🎯 Тестируем проверку неактивных пользователей...")

    # Запускаем задачу
    task = check_inactive_users.delay()

    # Ждем выполнения
    success, result = wait_for_task(task, "Проверка неактивных пользователей")

    return success


def run_complete_test():
    """Полный тест всех функций"""
    print_header("🚀 ПОЛНЫЙ ТЕСТ CELERY СИСТЕМЫ")
    print("Тестируем все задачи Celery без реальной отправки email")

    try:
        # 1. Настройка
        test_id = setup_test_environment()

        # 2. Создание данных
        users = create_test_users(test_id)
        owner = users[0]
        subscriber = users[1]
        inactive_user = users[2]

        course = create_test_course(owner, test_id)
        setup_subscriptions(course, [owner, subscriber])

        print_success("✅ Тестовые данные созданы!")

        # 3. Запуск тестов
        test_results = []

        # Тест 1: Уведомления о курсе
        test1_success = test_course_notification(course)
        test_results.append(("Уведомления о курсе", test1_success))

        # Тест 2: Уведомление о блокировке
        test2_success = test_block_notification(subscriber)
        test_results.append(("Уведомление о блокировке", test2_success))

        # Тест 3: Проверка неактивных пользователей
        test3_success = test_inactive_users_check()
        test_results.append(("Проверка неактивных", test3_success))

        # 4. Проверяем результаты
        print_header("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")

        all_passed = True
        for test_name, success in test_results:
            status = "✅ ПРОЙДЕН" if success else "❌ НЕ ПРОЙДЕН"
            print(f"{status}: {test_name}")
            if not success:
                all_passed = False

        # 5. Проверяем блокировку пользователя
        inactive_user.refresh_from_db()
        user_blocked = not inactive_user.is_active

        print(f"\n👤 Статус неактивного пользователя:")
        print(f"   Email: {inactive_user.email}")
        print(f"   is_active: {inactive_user.is_active}")
        print(f"   Заблокирован: {'✅ ДА' if user_blocked else '❌ НЕТ'}")

        if user_blocked:
            test_results.append(("Блокировка пользователя", True))
        else:
            test_results.append(("Блокировка пользователя", False))
            all_passed = False

        # 6. Итоги
        print_header("🎯 ИТОГИ")

        passed_count = sum(1 for _, success in test_results if success)
        total_count = len(test_results)

        print(f"✅ Пройдено тестов: {passed_count} из {total_count}")

        if all_passed:
            print_success("🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
            print("Система Celery работает корректно.")
        else:
            print_error(f"⚠️  Провалено тестов: {total_count - passed_count}")
            print("Некоторые функции требуют доработки.")

        return all_passed

    except Exception as e:
        print_error(f"ОШИБКА В ТЕСТЕ: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Очистка после теста"""
    print_header("🧹 ОЧИСТКА")

    # Удаляем тестовые данные
    deleted_users = User.objects.filter(email__contains='test_').delete()
    deleted_courses = Course.objects.filter(title__contains='Тестовый').delete()

    print(f"👤 Удалено пользователей: {deleted_users[0]}")
    print(f"📚 Удалено курсов: {deleted_courses[0]}")
    print_success("Очистка завершена!")


if __name__ == "__main__":
    print("=" * 80)
    print("🛠️  ТЕСТИРОВАНИЕ CELERY СИСТЕМЫ LMS")
    print("=" * 80)
    print("\nПеред тестированием убедитесь, что:")
    print("1. ✅ Redis запущен (команда: redis-server)")
    print("2. ✅ Celery Worker запущен (команда: celery -A config worker)")
    print("3. ⚠️  Django сервер НЕ требуется для этого теста")

    input("\nНажмите Enter для начала тестирования...")

    try:
        success = run_complete_test()

        if success:
            print("\n" + "=" * 80)
            print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("⚠️  ТЕСТИРОВАНИЕ ЗАВЕРШЕНО С ОШИБКАМИ")
            print("=" * 80)

    finally:
        # Всегда очищаем тестовые данные
        cleanup()

        print("\n" + "=" * 80)
        print("📋 ИНСТРУКЦИЯ ДЛЯ ПРОВЕРКИ В РЕЖИМЕ РАБОТЫ:")
        print("=" * 80)
        print("1. Для реальной отправки email в production:")
        print("   - Настройте SMTP в config/settings.py")
        print("   - Измените EMAIL_BACKEND на smtp")
        print("   - Добавьте реальные настройки email")
        print("\n2. Текущий режим: DEVELOPMENT")
        print("   - Все email только логируются")
        print("   - Никаких реальных отправок не происходит")
        print("   - Идеально для тестирования и разработки")
