from celery import Celery
from celery.schedules import crontab
from ..config import settings

# Här använder vi Redis som message broker
celery = Celery(
    "football_platform",
    broker=settings.REDIS_URL,  # Exempel på URL: redis://localhost:6379/0
    backend=settings.REDIS_URL,  # Om du också vill använda Redis för resultatlagring
)

# Optional: Om du har andra inställningar som result_backend, kan du lägga till dem här
celery.conf.update(
    broker_connection_retry_on_startup=True,
    task_routes={
        "app.tasks.*": {"queue": "default"}
    },
    beat_schedule={
        'sync-matches-every-5min': {
            'task': 'app.tasks.sync_matches',
            'schedule': 300.0,  # Every 5 minutes
        },
        'sync-completed-matches-daily': {
            'task': 'app.tasks.sync_completed_matches',
            'schedule': crontab(hour=0, minute=0),  # Daily at midnight
        },
        'sync-team-statistics-daily': {
            'task': 'app.tasks.sync_team_statistics',
            'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
        },
        'sync-player-statistics-daily': {
            'task': 'app.tasks.sync_player_statistics',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        }
    }
)