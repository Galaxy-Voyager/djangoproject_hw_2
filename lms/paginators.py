from rest_framework.pagination import PageNumberPagination


class CoursePagination(PageNumberPagination):
    """Пагинация для курсов"""
    page_size = 5  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для изменения количества элементов
    max_page_size = 20  # Максимальное количество элементов на странице


class LessonPagination(PageNumberPagination):
    """Пагинация для уроков"""
    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для изменения количества элементов
    max_page_size = 30  # Максимальное количество элементов на странице
