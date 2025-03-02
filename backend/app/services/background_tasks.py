from celery import shared_task
from ..database import SessionLocal
from .data_sync import DataSyncService
from ..api_service.football_api import FootballAPIService
import logging

logger = logging.getLogger(__name__)

@shared_task
def sync_data():
    """Daily task to sync all data"""
    logger.info("Starting daily data sync...")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_all()
        logger.info("Daily data sync completed successfully")
    except Exception as e:
        logger.error(f"Error during data sync: {str(e)}")
    finally:
        db.close() 