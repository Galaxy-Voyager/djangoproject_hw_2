# Используем официальный Python образ
FROM python:3.13-slim

# Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y \
        gcc \
        g++ \
        postgresql-client \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml poetry.lock* ./

# Устанавливаем poetry и зависимости
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Копируем остальные файлы проекта
COPY . .

# Создаем пользователя без привилегий
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Создаем директории для статики и медиа
RUN mkdir -p /app/static /app/media

# Команда по умолчанию
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
