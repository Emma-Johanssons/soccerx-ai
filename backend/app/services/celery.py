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
        'sync-static-data-daily': {
            'task': 'app.tasks.sync_static_data',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        },
        'sync-matches-every-5min': {
            'task': 'app.tasks.sync_matches',
            'schedule': 300.0,  # Every 5 minutes
        },
        'sync-statistics-daily': {
            'task': 'app.tasks.sync_statistics',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        },
        'daily-sync': {
            'task': 'app.services.background_tasks.sync_data',
            'schedule': crontab(hour=3),  # Runs at 3 AM every day
        },
    }
)