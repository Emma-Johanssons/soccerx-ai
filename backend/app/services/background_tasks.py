from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from ..database import SessionLocal
from .data_sync import DataSyncService
from ..api_service.football_api import FootballAPIService
import logging

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def sync_data():
    logger.info("Starting daily data sync...")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        await sync_service.sync_all()
        logger.info("Daily data sync completed successfully")
    except Exception as e:
        logger.error(f"Error during data sync: {str(e)}")
    finally:
        db.close()

def schedule_data_sync():
    # Run sync every day at 3 AM
    scheduler.add_job(sync_data, CronTrigger(hour=3))
    scheduler.start() 