import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Планировщик для периодических задач
app.conf.beat_schedule = {
    'check-inactive-users-monthly': {
        'task': 'users.tasks.check_inactive_users',
        'schedule': crontab(hour=0, minute=0),  # Ежедневно в полночь
    },
}

app.conf.timezone = 'UTC'
