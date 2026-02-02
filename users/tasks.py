from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def check_inactive_users():
    """
    Проверка пользователей, которые не заходили более месяца, и их блокировка
    """
    task_id = getattr(check_inactive_users.request, 'id', 'N/A') if hasattr(check_inactive_users, 'request') else 'N/A'

    logger.info(f"[TASK START] check_inactive_users - Task ID: {task_id}")
    print(f"\n{'=' * 80}")
    print(f"CELERY TASK STARTED: check_inactive_users")
    print(f"Task ID: {task_id}")
    print(f"{'=' * 80}")

    try:
        month_ago = timezone.now() - timedelta(days=30)
        print(f"Проверяем пользователей, не заходивших с {month_ago.date()}")

        # Ищем активных пользователей, которые не заходили более месяца
        # Исключаем суперпользователей
        inactive_users = User.objects.filter(
            is_active=True,
            last_login__lt=month_ago
        ).exclude(is_superuser=True)

        inactive_count = inactive_users.count()
        print(f"Найдено неактивных пользователей: {inactive_count}")

        if inactive_count == 0:
            result = "No inactive users found"
            print(f"{result}")
            return result

        blocked_count = 0
        results = []

        for user in inactive_users:
            print(f"\n👤 Обработка пользователя: {user.email} (ID: {user.id})")
            print(f"   Последний вход: {user.last_login.date() if user.last_login else 'Никогда'}")

            # Отправляем "уведомление" о блокировке
            notification_result = send_block_notification.delay(user.id)
            print(f"Задача уведомления отправлена: {notification_result.id}")

            # Блокируем пользователя
            user.is_active = False
            user.save(update_fields=['is_active'])
            blocked_count += 1

            user_status = f"Пользователь {user.email} заблокирован"
            results.append(user_status)
            print(f"{user_status}")

        result_msg = f"Заблокировано пользователей: {blocked_count}"
        print(f"\n{result_msg}")

        if results:
            print("Детали:")
            for res in results:
                print(f"   - {res}")

        logger.info(f"Task completed: {result_msg}")
        return result_msg

    except Exception as e:
        error_msg = f"Unexpected error in check_inactive_users: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"\n{error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


@shared_task
def send_block_notification(user_id):
    """
    Отправка уведомления пользователю о блокировке
    В разработке только логирует отправку
    """
    task_id = getattr(send_block_notification.request, 'id', 'N/A') if hasattr(send_block_notification,
                                                                               'request') else 'N/A'

    logger.info(f"[TASK START] send_block_notification - User ID: {user_id}, Task ID: {task_id}")
    print(f"\n{'=' * 80}")
    print(f"CELERY TASK STARTED: send_block_notification")
    print(f"Task ID: {task_id}")
    print(f"User ID: {user_id}")
    print(f"{'=' * 80}")

    try:
        # Получаем пользователя
        try:
            user = User.objects.get(id=user_id)
            logger.info(f"Found user: {user.email} (ID: {user.id})")
            print(f"Найден пользователь: {user.email} (ID: {user.id})")
        except User.DoesNotExist:
            error_msg = f"User with ID {user_id} not found"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        # Проверяем email
        user_email = getattr(user, 'email', '')

        if not user_email:
            error_msg = f"User {user_id} has no email"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        if not isinstance(user_email, str):
            error_msg = f"User {user_id} email is not string: {type(user_email)}"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        clean_email = user_email.strip()

        if not clean_email:
            error_msg = f"User {user_id} has empty email"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        if '@' not in clean_email:
            error_msg = f"User {user_id} has invalid email: '{clean_email}'"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        print(f"Email пользователя: {clean_email}")

        # Формируем сообщение
        user_name = user.first_name or clean_email.split('@')[0]
        subject = 'Ваш аккаунт был заблокирован'
        message_content = f'Добрый день, {user_name}!\n\n'
        message_content += 'Ваш аккаунт был временно заблокирован, так как вы не заходили в систему более 30 дней.\n'
        message_content += 'Для восстановления доступа обратитесь в службу поддержки.\n\n'
        message_content += 'С уважением, Команда LMS Platform'

        # Логируем "отправку" email
        print(f"\n{'=' * 80}")
        print("BLOCK NOTIFICATION SIMULATION (DEVELOPMENT MODE)")
        print(f"{'=' * 80}")
        print(f"От: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lms.local')}")
        print(f"Кому: {clean_email}")
        print(f"Тема: {subject}")
        print(f"Сообщение ({len(message_content)} символов):")
        print("-" * 40)
        print(message_content)
        print("-" * 40)
        print(f"{'=' * 80}")

        # Записываем в лог
        logger.info(f"Would send block notification to {clean_email}")

        # Возвращаем успешный результат
        result_msg = f"Block notification prepared for {clean_email}"
        print(f"\n{result_msg}")
        logger.info(f"Task completed: {result_msg}")

        return result_msg

    except Exception as e:
        error_msg = f"Unexpected error in send_block_notification: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"\n{error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg
