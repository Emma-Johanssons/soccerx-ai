import os
import time
import redis
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

def wait_for_redis():
    """Wait for Redis to be available"""
    redis_host = os.getenv('REDIS_HOST', 'redis')
    redis_port = int(os.getenv('REDIS_PORT', 6379))
    
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            r = redis.Redis(host=redis_host, port=redis_port)
            r.ping()
            logger.info("Successfully connected to Redis")
            return
        except redis.exceptions.ConnectionError:
            logger.warning(f"Redis not available yet, retrying in {retry_interval} seconds... ({i+1}/{max_retries})")
            time.sleep(retry_interval)
    
    logger.error("Could not connect to Redis after multiple attempts")
    raise Exception("Redis connection failed")

# Wait for Redis to be available
wait_for_redis()

# Configure Celery
app = Celery(
    'football_platform',
    broker=f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/0",
)

# Configure Celery with better retry settings
app.conf.update(
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=30,
    broker_pool_limit=10,
    broker_heartbeat=10,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'sync-live-matches': {
            'task': 'app.tasks.tasks.sync_live_matches',
            'schedule': 60.0,  # Every minute
        },
        'sync-upcoming-matches': {
            'task': 'app.tasks.tasks.sync_upcoming_matches',
            'schedule': crontab(hour=6, minute=0),  # Every day at 6 AM
        },
        'sync-completed-matches': {
            'task': 'app.tasks.tasks.sync_completed_matches',
            'schedule': crontab(hour=23, minute=30),  # Every day at 11:30 PM
        },
        'sync-daily-data': {
            'task': 'app.tasks.tasks.sync_daily_data',
            'schedule': crontab(hour='*/12', minute=0),  # Every 12 hours
        },
        'sync-static-data': {
            'task': 'app.tasks.tasks.sync_static_data',
            'schedule': crontab(hour=4, minute=0, day_of_week=1),  # Weekly on Monday at 4 AM
        },
        'sync-team-data': {
            'task': 'app.tasks.tasks.sync_team_data',
            'schedule': crontab(hour=4, minute=0, day_of_week=1),
        },
        'sync-team-statistics': {
            'task': 'app.tasks.tasks.sync_team_statistics',
            'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
        },
    }
)

# Make sure tasks are registered
app.autodiscover_tasks(['app'])

# For compatibility with existing code
celery = app

# Test tasks
@app.task(name='test.ping')
def ping():
    """Simple ping task for testing"""
    logger.info("Ping task executed")
    return "pong"

@app.task(name='test.debug')
def debug_task(self):
    """Debug task that prints request info"""
    logger.info(f'Request: {self.request!r}')
    return "Debug task completed"

if __name__ == '__main__':
    app.start() 