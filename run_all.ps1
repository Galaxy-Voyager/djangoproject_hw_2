# Скрипт для запуска всех сервисов
Write-Host "=== ЗАПУСК LMS ПЛАТФОРМЫ ===" -ForegroundColor Cyan

# Запускаем Redis в новом окне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Redis сервер...' -ForegroundColor Yellow; redis-server"

# Ждем секунду для запуска Redis
Start-Sleep -Seconds 2

# Запускаем Celery worker в новом окне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Celery Worker...' -ForegroundColor Green; .\venv\Scripts\Activate.ps1; celery -A config worker --loglevel=info --pool=solo"

# Запускаем Celery beat в новом окне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host 'Celery Beat...' -ForegroundColor Green; .\venv\Scripts\Activate.ps1; celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler"

# Запускаем Django сервер в текущем окне
Write-Host "Django сервер..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1
python manage.py runserver