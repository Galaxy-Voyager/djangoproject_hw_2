# Скрипт для запуска Celery worker и beat
Write-Host "Запуск Redis..." -ForegroundColor Green
Start-Process redis-server

Write-Host "Запуск Celery worker..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1
celery -A config worker --loglevel=info --pool=solo

Write-Host "Запуск Celery beat..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1
celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler