from app.base_celery import app
import logging

logger = logging.getLogger(__name__)

@app.task
def test_redis_connection():
    """Simple task to test Redis connectivity"""
    logger.info("Test task executed successfully!")
    return "Test task completed" 