import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('claverica')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Scheduled tasks
app.conf.beat_schedule = {
    'calculate-daily-interest': {
        'task': 'savings.tasks.calculate_interest',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'update-crypto-prices': {
        'task': 'crypto.tasks.update_prices',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
