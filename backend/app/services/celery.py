from celery import Celery
from celery.schedules import crontab
from ..config import settings

# Här använder vi Redis som message broker
celery = Celery(
    "football_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Optional: Om du har andra inställningar som result_backend, kan du lägga till dem här
celery.conf.update(
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.tasks.*": {"queue": "default"}
    },
    beat_schedule={
        'sync-todays-matches': {
            'task': 'app.tasks.sync_todays_matches',
            'schedule': crontab(minute='*/30')  # Every 30 minutes
        },
        'sync-live-matches': {
            'task': 'app.tasks.sync_live_matches',
            'schedule': crontab(minute='*/1')  # Every minute
        },
        'sync-completed-matches': {
            'task': 'app.tasks.sync_completed_matches',
            'schedule': crontab(hour='*/4')  # Every 4 hours
        }
    }
)