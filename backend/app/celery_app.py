from celery import Celery
from celery.schedules import crontab
from .config import settings
import logging

logger = logging.getLogger(__name__)

celery = Celery(
    "football_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks',
    ]
)

celery.conf.update(
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    task_routes={
        "app.tasks.*": {"queue": "default"}
    },
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Beat schedule
    beat_schedule={
        # Live data updates
        'sync-live-matches': {
            'task': 'app.tasks.sync_live_matches',
            'schedule': 60.0,  # Run every minute
        },
        'sync-todays-matches': {
            'task': 'app.tasks.sync_todays_matches',
            'schedule': crontab(minute='0', hour='0'),  # Run at midnight
        },
        
        # Daily updates
        'sync-completed-matches': {
            'task': 'app.tasks.sync_completed_matches',
            'schedule': crontab(hour='*/4')  # Every 4 hours
        },
        'sync-daily-data': {
            'task': 'app.tasks.sync_daily_data',
            'schedule': crontab(minute=0, hour=0)  # Midnight
        },
        'sync-player-statistics': {
            'task': 'app.tasks.sync_player_statistics',
            'schedule': crontab(minute=0, hour=1)  # 1 AM
        },
        'sync-match-statistics': {
            'task': 'app.tasks.sync_match_statistics',
            'schedule': crontab(minute=0, hour=6)  # 6 AM
        },
        
        # Weekly updates
        'sync-static-data': {
            'task': 'app.tasks.sync_static_data',
            'schedule': crontab(minute=0, hour=0, day_of_week=1)  # Monday at midnight
        },
        'sync-team-data': {
            'task': 'app.tasks.sync_team_data',
            'schedule': crontab(minute=0, hour=2, day_of_week=1)  # Monday at 2 AM
        }
    }
)

@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    logger.info("Celery beat schedule initialized")

@celery.task(bind=True)
def debug_task(self):
    logger.info(f'Request: {self.request!r}')

if __name__ == '__main__':
    celery.start()