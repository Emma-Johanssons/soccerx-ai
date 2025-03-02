from app.base_celery import app
import logging

logger = logging.getLogger(__name__)

# Remove the duplicate fetch_team_statistics function
# We'll use the one from tasks.py instead 