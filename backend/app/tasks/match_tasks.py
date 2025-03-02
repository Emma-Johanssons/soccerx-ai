from app.base_celery import app
import logging

logger = logging.getLogger(__name__)

@app.task(name='app.tasks.sync_todays_matches')
def sync_todays_matches():
    """Sync today's matches task"""
    logger.info("Starting sync_todays_matches task")
    return "Sync today's matches completed"

@app.task(name='app.tasks.sync_live_matches')
def sync_live_matches():
    """Sync live matches task"""
    logger.info("Starting sync_live_matches task")
    return "Sync live matches completed" 