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
        'sync-league-data': {
            'task': 'app.tasks.sync_league_data',
            'schedule': crontab(hour=0, minute=0)  # Run at midnight
        },
        'sync-team-statistics': {
            'task': 'app.tasks.sync_team_statistics',
            'schedule': crontab(hour=1, minute=0)  # Run at 1 AM
        },
        'sync-player-statistics': {
            'task': 'app.tasks.sync_player_statistics',
            'schedule': crontab(hour=2, minute=0)  # Run at 2 AM
        }
    }
)