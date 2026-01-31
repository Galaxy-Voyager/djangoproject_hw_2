from rest_framework import serializers
from urllib.parse import urlparse
import re


def validate_youtube_url(value):
    """Функция-валидатор для проверки ссылок на YouTube"""
    if not value:
        return value

    # Проверяем, что value - это строка, а не словарь
    if not isinstance(value, str):
        raise serializers.ValidationError("URL должен быть строкой")

    parsed_url = urlparse(value)

    # Проверяем, что домен youtube.com или youtu.be
    if 'youtube.com' not in parsed_url.netloc and 'youtu.be' not in parsed_url.netloc:
        raise serializers.ValidationError(
            "Разрешены только ссылки на YouTube (youtube.com или youtu.be)"
        )

    # Дополнительная проверка на валидный YouTube URL
    youtube_patterns = [
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+',
        r'(https?://)?(m\.)?(youtube\.com|youtu\.be)/.+'
    ]

    is_valid = any(re.match(pattern, value) for pattern in youtube_patterns)
    if not is_valid:
        raise serializers.ValidationError(
            "Некорректная ссылка на YouTube"
        )

    return value


class YouTubeURLValidator:
    """Валидатор-класс для проверки ссылок на YouTube"""

    def __init__(self, field='video_link'):
        self.field = field

    def __call__(self, attrs):
        """Метод вызывается при валидации всего словаря атрибутов"""
        url = attrs.get(self.field)

        if url:
            validate_youtube_url(url)

        return attrs
