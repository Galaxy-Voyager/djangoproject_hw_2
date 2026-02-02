from celery import shared_task
from django.conf import settings
from .models import Course, Subscription
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notification(course_id):
    """
    Асинхронная отправка уведомлений об обновлении курса всем подписчикам
    В разработке только логирует отправку email
    """
    task_id = getattr(send_course_update_notification.request, 'id', 'N/A') if hasattr(send_course_update_notification,
                                                                                       'request') else 'N/A'

    logger.info(f"[TASK START] send_course_update_notification - Course ID: {course_id}, Task ID: {task_id}")
    print(f"\n{'=' * 80}")
    print(f"CELERY TASK STARTED: send_course_update_notification")
    print(f"Task ID: {task_id}")
    print(f"Course ID: {course_id}")
    print(f"{'=' * 80}")

    try:
        # 1. Получаем курс
        try:
            course = Course.objects.get(id=course_id)
            logger.info(f"Found course: {course.title} (ID: {course.id})")
            print(f"Найден курс: '{course.title}' (ID: {course.id})")
        except Course.DoesNotExist:
            error_msg = f"Course with ID {course_id} not found"
            logger.error(error_msg)
            print(f"{error_msg}")
            return error_msg

        # 2. Получаем подписчиков
        subscribers = Subscription.objects.filter(course=course).select_related('user')
        subscriber_count = subscribers.count()
        logger.info(f"Found {subscriber_count} subscribers for course {course.id}")
        print(f"📊 Найдено подписчиков: {subscriber_count}")

        if subscriber_count == 0:
            result = "No subscribers for this course"
            logger.info(result)
            print(f"ℹ️  {result}")
            return result

        # 3. Собираем валидные email
        valid_recipients = []
        skipped_users = []

        for index, sub in enumerate(subscribers, 1):
            user = sub.user

            if not user:
                skipped_msg = f"Subscription {sub.id}: No user object"
                skipped_users.append(skipped_msg)
                logger.warning(skipped_msg)
                continue

            user_email = getattr(user, 'email', None)

            # Проверяем email
            if not user_email:
                skipped_msg = f"User {user.id}: No email attribute"
                skipped_users.append(skipped_msg)
                logger.warning(skipped_msg)
                continue

            if not isinstance(user_email, str):
                skipped_msg = f"User {user.id}: Email is not string ({type(user_email)})"
                skipped_users.append(skipped_msg)
                logger.warning(skipped_msg)
                continue

            clean_email = user_email.strip()

            if not clean_email:
                skipped_msg = f"User {user.id}: Empty email after stripping"
                skipped_users.append(skipped_msg)
                logger.warning(skipped_msg)
                continue

            if '@' not in clean_email:
                skipped_msg = f"User {user.id}: Invalid email format (no @): '{clean_email}'"
                skipped_users.append(skipped_msg)
                logger.warning(skipped_msg)
                continue

            valid_recipients.append(clean_email)
            print(f"Подписчик {index}: {clean_email}")

        # 4. Логируем пропущенных
        if skipped_users:
            print(f"\nПропущено пользователей: {len(skipped_users)}")
            for skipped in skipped_users[:5]:  # Показываем только первые 5
                print(f"   - {skipped}")
            if len(skipped_users) > 5:
                print(f"   ... и еще {len(skipped_users) - 5}")

        # 5. Проверяем результаты
        if not valid_recipients:
            result = "No valid email recipients found"
            logger.warning(result)
            print(f"\n{result}")
            return result

        print(f"\nВалидных получателей: {len(valid_recipients)}")

        # 6. Формируем "email" сообщение (только логирование)
        subject = f'Обновление курса: {course.title}'
        message_content = f'Добрый день!\n\nКурс "{course.title}" был обновлен.\n'

        if course.description:
            desc_preview = course.description[:200] + ('...' if len(course.description) > 200 else '')
            message_content += f'Описание: {desc_preview}\n\n'
        else:
            message_content += 'Нет описания\n\n'

        message_content += 'Перейдите в личный кабинет, чтобы ознакомиться с изменениями.\n'
        message_content += 'С уважением, Команда LMS Platform'

        # 7. Логируем "отправку" email
        print(f"\n{'=' * 80}")
        print("EMAIL SIMULATION (DEVELOPMENT MODE)")
        print(f"{'=' * 80}")
        print(f"От: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lms.local')}")
        print(f"Кому: {valid_recipients}")
        print(f"Тема: {subject}")
        print(f"Сообщение ({len(message_content)} символов):")
        print("-" * 40)
        print(message_content[:500] + ('...' if len(message_content) > 500 else ''))
        print("-" * 40)
        print(f"{'=' * 80}")

        # 8. Записываем в лог
        logger.info(f"Would send email to {len(valid_recipients)} recipients for course {course.id}")
        for recipient in valid_recipients:
            logger.debug(f"  Recipient: {recipient}")

        # 9. Возвращаем успешный результат
        result_msg = f"Email notification prepared for {len(valid_recipients)} recipient(s)"
        print(f"\n{result_msg}")
        logger.info(f"Task completed: {result_msg}")

        return result_msg

    except Exception as e:
        error_msg = f"Unexpected error in send_course_update_notification: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"\n{error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


@shared_task
def check_course_updates_and_notify():
    """
    Проверка обновлений курсов за последние 4 часа и отправка уведомлений
    """
    logger.info("Task started: check_course_updates_and_notify")
    print("\n" + "=" * 80)
    print("Проверка обновлений курсов за последние 4 часа")

    four_hours_ago = timezone.now() - timedelta(hours=4)
    updated_courses = Course.objects.filter(
        updated_at__gte=four_hours_ago
    ).exclude(updated_at__isnull=True)

    course_count = updated_courses.count()
    print(f"Найдено обновленных курсов: {course_count}")

    if course_count == 0:
        result = "No courses updated in the last 4 hours"
        print(f"{result}")
        return result

    results = []
    for course in updated_courses:
        print(f"  📚 Курс: '{course.title}' (обновлен: {course.updated_at})")
        # Запускаем задачу отправки уведомления для этого курса
        task = send_course_update_notification.delay(course.id)
        results.append(f"Курс '{course.title}': задача {task.id} отправлена")

    result_msg = f"Запущено {len(results)} задач на отправку уведомлений"
    print(f"\n{result_msg}")
    return result_msg
