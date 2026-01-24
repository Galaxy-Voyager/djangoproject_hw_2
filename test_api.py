import json

import requests

BASE_URL = "http://127.0.0.1:8000/api/"


def test_api():
    print("=== Тестирование API LMS ===")

    # 1. Тестирование курсов
    print("\n1. Тестирование курсов:")

    # Создание курса
    course_data = {
        "title": "Python для начинающих",
        "description": "Курс по основам Python",
    }
    response = requests.post(f"{BASE_URL}courses/", json=course_data)
    print(f"Создание курса: {response.status_code}")
    if response.status_code == 201:
        course = response.json()
        print(f"Создан курс: {course}")

    # Получение списка курсов
    response = requests.get(f"{BASE_URL}courses/")
    print(f"Получение списка курсов: {response.status_code}")
    if response.status_code == 200:
        courses = response.json()
        print(f"Найдено курсов: {len(courses)}")

    # 2. Тестирование уроков
    print("\n2. Тестирование уроков:")

    # Создание урока
    lesson_data = {
        "title": "Введение в Python",
        "description": "Первое знакомство с Python",
        "video_link": "https://youtube.com/watch?v=example123",
        "course": 1,  # ID курса, созданного выше
    }
    response = requests.post(f"{BASE_URL}lessons/", json=lesson_data)
    print(f"Создание урока: {response.status_code}")

    # Получение списка уроков
    response = requests.get(f"{BASE_URL}lessons/")
    print(f"Получение списка уроков: {response.status_code}")
    if response.status_code == 200:
        lessons = response.json()
        print(f"Найдено уроков: {len(lessons)}")

    # 3. Тестирование пользователей
    print("\n3. Тестирование пользователей:")
    response = requests.get(f"{BASE_URL}users/")
    print(f"Получение списка пользователей: {response.status_code}")

    print("\n=== Тестирование завершено ===")


if __name__ == "__main__":
    test_api()
