from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import Group
from users.models import User
from .models import Course, Lesson, Subscription


class LMSTestCase(APITestCase):
    """Базовый тестовый класс для LMS"""

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем группы
        self.moderator_group, _ = Group.objects.get_or_create(name='moderators')
        self.student_group, _ = Group.objects.get_or_create(name='students')

        # Создаем пользователей
        self.moderator = User.objects.create_user(
            email='moderator@test.com',
            password='testpass123',
            first_name='Moderator',
            last_name='Test'
        )
        self.moderator.groups.add(self.moderator_group)

        self.student = User.objects.create_user(
            email='student@test.com',
            password='testpass123',
            first_name='Student',
            last_name='Test'
        )
        self.student.groups.add(self.student_group)

        self.student2 = User.objects.create_user(
            email='student2@test.com',
            password='testpass123',
            first_name='Student2',
            last_name='Test'
        )
        self.student2.groups.add(self.student_group)

        # Создаем курсы
        self.course1 = Course.objects.create(
            title='Тестовый курс 1',
            description='Описание тестового курса 1',
            owner=self.student
        )

        self.course2 = Course.objects.create(
            title='Тестовый курс 2',
            description='Описание тестового курса 2',
            owner=self.student2
        )

        # Создаем уроки
        self.lesson1 = Lesson.objects.create(
            title='Тестовый урок 1',
            description='Описание тестового урока 1',
            course=self.course1,
            video_link='https://www.youtube.com/watch?v=test1',
            owner=self.student
        )

        self.lesson2 = Lesson.objects.create(
            title='Тестовый урок 2',
            description='Описание тестового урока 2',
            course=self.course1,
            video_link='https://www.youtube.com/watch?v=test2',
            owner=self.student
        )


class CourseCRUDTestCase(LMSTestCase):
    """Тесты CRUD операций для курсов"""

    def test_student_can_create_course(self):
        """Тест: студент может создать курс"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:course-list')
        data = {
            'title': 'Новый курс',
            'description': 'Описание нового курса'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Новый курс')
        self.assertEqual(Course.objects.count(), 3)  # 2 из setUp + 1 новый

    def test_moderator_cannot_create_course(self):
        """Тест: модератор НЕ может создать курс"""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('lms:course-list')
        data = {
            'title': 'Курс от модератора',
            'description': 'Описание курса от модератора'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_view_own_courses(self):
        """Тест: студент видит только свои курсы"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:course-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Только свой курс
        self.assertEqual(response.data['results'][0]['title'], 'Тестовый курс 1')

    def test_moderator_can_view_all_courses(self):
        """Тест: модератор видит все курсы"""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('lms:course-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # Все курсы

    def test_student_can_update_own_course(self):
        """Тест: студент может обновить свой курс"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:course-detail', args=[self.course1.id])
        data = {
            'title': 'Обновленный курс',
            'description': 'Обновленное описание'
        }

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, 'Обновленный курс')

    def test_student_cannot_update_other_course(self):
        """Тест: студент НЕ может обновить чужой курс"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:course-detail', args=[self.course2.id])
        data = {'title': 'Попытка изменить чужой курс'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_moderator_can_update_any_course(self):
        """Тест: модератор может обновить любой курс"""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('lms:course-detail', args=[self.course1.id])
        data = {'title': 'Курс обновлен модератором'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course1.refresh_from_db()
        self.assertEqual(self.course1.title, 'Курс обновлен модератором')

    def test_student_can_delete_own_course(self):
        """Тест: студент может удалить свой курс"""
        Lesson.objects.filter(course=self.course1).delete()

        self.client.force_authenticate(user=self.student)

        url = reverse('lms:course-detail', args=[self.course1.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Course.objects.count(), 1)  # Остался только course2

    def test_moderator_cannot_delete_course(self):
        """Тест: модератор НЕ может удалить курс"""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('lms:course-detail', args=[self.course1.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LessonCRUDTestCase(LMSTestCase):
    """Тесты CRUD операций для уроков"""

    def test_student_can_create_lesson(self):
        """Тест: студент может создать урок"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:lesson-list-create')
        data = {
            'title': 'Новый урок',
            'description': 'Описание нового урока',
            'course': self.course1.id,
            'video_link': 'https://www.youtube.com/watch?v=newlesson'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 3)  # 2 из setUp + 1 новый

    def test_youtube_validator_works(self):
        """Тест: валидатор YouTube ссылок работает"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:lesson-list-create')
        data = {
            'title': 'Урок с невалидной ссылкой',
            'description': 'Описание урока',
            'course': self.course1.id,
            'video_link': 'https://vimeo.com/123456'  # Не YouTube ссылка
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_link', response.data)

    def test_moderator_cannot_create_lesson(self):
        """Тест: модератор НЕ может создать урок"""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('lms:lesson-list-create')
        data = {
            'title': 'Урок от модератора',
            'description': 'Описание урока',
            'course': self.course1.id,
            'video_link': 'https://www.youtube.com/watch?v=moderator'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_pagination_works(self):
        """Тест: пагинация работает для уроков"""
        self.client.force_authenticate(user=self.student)

        # Создаем больше уроков для тестирования пагинации
        for i in range(15):
            Lesson.objects.create(
                title=f'Урок {i}',
                description=f'Описание урока {i}',
                course=self.course1,
                video_link=f'https://www.youtube.com/watch?v=lesson{i}',
                owner=self.student
            )

        url = reverse('lms:lesson-list-create')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # page_size по умолчанию

        # Тестируем изменение page_size через параметр
        response = self.client.get(f'{url}?page_size=5')
        self.assertEqual(len(response.data['results']), 5)


class SubscriptionTestCase(LMSTestCase):
    """Тесты функционала подписок"""

    def test_user_can_subscribe_to_course(self):
        """Тест: пользователь может подписаться на курс"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:subscriptions')
        data = {'course_id': self.course1.id}

        # Подписываемся
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Подписка добавлена', response.data['message'])
        self.assertTrue(Subscription.objects.filter(user=self.student, course=self.course1).exists())

        # Проверяем, что в ответе курса есть признак подписки
        course_url = reverse('lms:course-detail', args=[self.course1.id])
        course_response = self.client.get(course_url)
        self.assertTrue(course_response.data['is_subscribed'])

    def test_user_can_unsubscribe_from_course(self):
        """Тест: пользователь может отписаться от курса"""
        # Сначала создаем подписку
        Subscription.objects.create(user=self.student, course=self.course1)

        self.client.force_authenticate(user=self.student)

        url = reverse('lms:subscriptions')
        data = {'course_id': self.course1.id}

        # Отписываемся
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Подписка удалена', response.data['message'])
        self.assertFalse(Subscription.objects.filter(user=self.student, course=self.course1).exists())

    def test_subscription_toggle_works(self):
        """Тест: переключение подписки работает"""
        self.client.force_authenticate(user=self.student)

        url = reverse('lms:subscriptions')
        data = {'course_id': self.course1.id}

        # Первый запрос - подписаться
        response1 = self.client.post(url, data, format='json')
        self.assertIn('Подписка добавлена', response1.data['message'])

        # Второй запрос - отписаться
        response2 = self.client.post(url, data, format='json')
        self.assertIn('Подписка удалена', response2.data['message'])

        # Третий запрос - снова подписаться
        response3 = self.client.post(url, data, format='json')
        self.assertIn('Подписка добавлена', response3.data['message'])

    def test_user_can_view_own_subscriptions(self):
        """Тест: пользователь может просмотреть свои подписки"""
        # Создаем несколько подписок
        Subscription.objects.create(user=self.student, course=self.course1)
        Subscription.objects.create(user=self.student, course=self.course2)

        self.client.force_authenticate(user=self.student)

        url = reverse('lms:subscriptions')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_course_serializer_includes_subscription_status(self):
        """Тест: сериализатор курса включает статус подписки"""
        # Создаем подписку
        Subscription.objects.create(user=self.student, course=self.course1)

        self.client.force_authenticate(user=self.student)

        # Проверяем список курсов
        list_url = reverse('lms:course-list')
        list_response = self.client.get(list_url)

        # Находим наш курс в результатах
        for course in list_response.data['results']:
            if course['id'] == self.course1.id:
                self.assertTrue(course['is_subscribed'])
                break

        # Проверяем детали курса
        detail_url = reverse('lms:course-detail', args=[self.course1.id])
        detail_response = self.client.get(detail_url)
        self.assertTrue(detail_response.data['is_subscribed'])
