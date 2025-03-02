from app.base_celery import app
import logging
from app.database import SessionLocal
from app.api_service.football_api import FootballAPIService
from app.services.data_sync import DataSyncService
from datetime import datetime, timedelta
from app.sql_models.models import Team, Match, LastSync
logger = logging.getLogger(__name__)

@app.task
def fetch_team_statistics(team_id: int):
    """Fetch statistics for a specific team"""
    logger.info(f"Starting fetch_team_statistics task for team {team_id}")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        stats = football_api.get_team_statistics(team_id)
        # Store in database
        logger.info(f"Successfully fetched statistics for team {team_id}")
        return stats
    except Exception as e:
        logger.error(f"Error fetching team statistics: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_todays_matches():
    """Sync today's matches task"""
    logger.info("Starting sync_todays_matches task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_todays_matches()
        logger.info("Today's matches synced successfully")
        return "Sync today's matches completed"
    except Exception as e:
        logger.error(f"Error syncing today's matches: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_static_data():
    """Weekly sync of static data"""
    logger.info("Starting sync_static_data task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Sync all static data
        sync_service.sync_positions()
        sync_service.sync_countries()
        sync_service.sync_leagues()
        sync_service.sync_event_types()
        sync_service.sync_match_statuses()
        
        logger.info("Static data sync completed successfully")
        return "Sync static data completed"
    except Exception as e:
        logger.error(f"Error syncing static data: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_daily_data():
    """12-hour sync of standings and statistics"""
    logger.info("Starting sync_daily_data task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Sync teams and players
        sync_service.sync_teams()
        sync_service.sync_players()
        
        # Sync team statistics for all teams
        teams = db.query(Team).all()
        for team in teams:
            try:
                sync_service.fetch_and_store_team_statistics(team.id)
            except Exception as e:
                logger.error(f"Error syncing statistics for team {team.id}: {str(e)}")
                continue
        
        logger.info("Daily data sync completed successfully")
        return "Sync daily data completed"
    except Exception as e:
        logger.error(f"Error syncing daily data: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_live_matches():
    """Sync live matches task"""
    logger.info("Starting sync_live_matches task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_live_matches()
        logger.info("Live matches synced successfully")
        return "Sync live matches completed"
    except Exception as e:
        logger.error(f"Error syncing live matches: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_daily_matches():
    """Sync matches for today"""
    logger.info("Starting sync_daily_matches task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Make sure we're actually saving to the database
        result = sync_service.sync_daily_matches()
        
        # Explicitly commit the transaction
        db.commit()
        
        # Update the last_sync table
        last_sync = db.query(LastSync).filter(LastSync.task_name == "sync_daily_matches").first()
        if last_sync:
            last_sync.last_run = datetime.now()
        else:
            last_sync = LastSync(task_name="sync_daily_matches", last_run=datetime.now())
            db.add(last_sync)
        db.commit()
        
        logger.info(f"Daily matches synced successfully: {result}")
        return f"Sync daily matches completed: {result}"
    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing daily matches: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_team_data():
    """Sync team data"""
    logger.info("Starting sync_team_data task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_teams()
        logger.info("Team data sync completed successfully")
        return "Sync team data completed"
    except Exception as e:
        logger.error(f"Error syncing team data: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_all_data():
    """Sync all data"""
    logger.info("Starting sync_all_data task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Run sync_all method
        sync_service.sync_all()
        
        logger.info("All data sync completed successfully")
        return "Sync all data completed"
    except Exception as e:
        logger.error(f"Error syncing all data: {str(e)}")
        raise
    finally:
        db.close()

@app.task
def sync_statistics():
    """Sync statistics task"""
    logger.info("Starting sync_statistics task")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Sync team and player statistics
        sync_service.sync_team_statistics()
        sync_service.sync_player_statistics()
        
        logger.info("Statistics synced successfully")
        return "Sync statistics completed"
    except Exception as e:
        logger.error(f"Error syncing statistics: {str(e)}")
        raise
    finally:
        db.close() 