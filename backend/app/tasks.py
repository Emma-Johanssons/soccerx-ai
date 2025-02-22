from celery import shared_task
from app.database import SessionLocal
from app.api_service.football_api import FootballAPIService
from datetime import datetime, timedelta
import logging
from app.sql_models.models import Match, Team, MatchEvent, Player
from app.services.data_sync import DataSyncService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

MAJOR_LEAGUES = {
    'DFB Pokal': {'id': 529, 'season': 2024},
    'Copa del Rey': {'id': 143, 'season': 2024},
    'Premier League': {'id': 39, 'season': 2024},
    'Bundesliga': {'id': 78, 'season': 2024},
    'LaLiga': {'id': 140, 'season': 2024},
    'Serie A': {'id': 135, 'season': 2024},
    'Ligue 1': {'id': 61, 'season': 2024},
    'Champions League': {'id': 2, 'season': 2024},
    'Europa League': {'id': 3, 'season': 2024}
}

@shared_task
def sync_static_data():
    """Sync leagues, teams, and players data"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_countries()
        sync_service.sync_leagues()
        sync_service.sync_teams()
        logger.info("Static data sync completed")
    finally:
        db.close()

@shared_task
def sync_matches():
    """Sync live and upcoming matches"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        matches = football_api.get_matches()
        # Add logic to store matches in database
        logger.info("Matches sync completed")
    finally:
        db.close()

@shared_task
def sync_statistics():
    """Daily task to sync statistics for all teams and players"""
    db = SessionLocal()
    try:
        sync_service = DataSyncService(db, FootballAPIService())
        
        # Sync team statistics
        teams = db.query(Team).all()
        for team in teams:
            sync_service.fetch_and_store_team_statistics(team.id)
            
        # Sync player statistics
        players = db.query(Player).all()
        for player in players:
            sync_service.fetch_and_store_player_statistics(player.id)
            
    finally:
        db.close()

@shared_task
def fetch_team_statistics(team_id: int):
    """Fetch statistics for a specific team"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        stats = football_api.get_team_statistics(team_id)
        # Store in database
        return stats
    finally:
        db.close()

@shared_task
def sync_all_data():
    """Sync all data using DataSyncService"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_all()
        logger.info("Successfully synced all data")
    except Exception as e:
        logger.error(f"Error in sync_all_data: {str(e)}")
        raise
    finally:
        db.close()

@shared_task
def sync_completed_matches():
    """Sync completed matches from yesterday"""
    db = SessionLocal()
    try:
        api = FootballAPIService()
        yesterday = datetime.now().date() - timedelta(days=1)
        
        # Get yesterday's completed matches
        matches = api.get_matches(date=yesterday, status="FT")
        
        if matches and 'response' in matches:
            for match_data in matches['response']:
                # Update match details including events and statistics
                update_match_details_in_db(db, match_data)
        
        db.commit()
        logger.info(f"Successfully synced completed matches for {yesterday}")
    except Exception as e:
        logger.error(f"Error syncing completed matches: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@shared_task
def sync_team_data():
    """Sync team data for major leagues"""
    db = SessionLocal()
    try:
        api = FootballAPIService()
        
        # Update teams for major leagues
        for league_id in MAJOR_LEAGUES.values():
            teams = api.get_teams(league_id=league_id)
            if teams and 'response' in teams:
                for team_data in teams['response']:
                    update_team_in_db(db, team_data)
        
        db.commit()
        logger.info("Successfully synced team data")
    except Exception as e:
        logger.error(f"Error syncing team data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

@shared_task
def sync_team_statistics(team_id: int):
    """Sync statistics for a specific team"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_team_statistics(team_id)
    finally:
        db.close()

@shared_task
def sync_player_statistics(player_id: int):
    """Sync statistics for a specific player"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_player_statistics(player_id)
    finally:
        db.close()

@shared_task
def sync_daily_data():
    """Daily sync of completed matches and updates to team/player data"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_completed_matches()
        sync_service.sync_teams()
        sync_service.sync_players()
    finally:
        db.close()

def update_match_in_db(db, match_data):
    """Update or create match in database"""
    try:
        fixture = match_data['fixture']
        match = db.query(Match).filter_by(api_match_id=fixture['id']).first()
        
        if not match:
            match = Match(
                api_match_id=fixture['id'],
                home_team_id=match_data['teams']['home']['id'],
                away_team_id=match_data['teams']['away']['id'],
                league_id=match_data['league']['id'],
                match_date=datetime.fromtimestamp(fixture['timestamp']),
                status=fixture['status']['short'],
                home_score=match_data['goals']['home'],
                away_score=match_data['goals']['away']
            )
            db.add(match)
        else:
            match.status = fixture['status']['short']
            match.home_score = match_data['goals']['home']
            match.away_score = match_data['goals']['away']
            
        return match
    except Exception as e:
        logger.error(f"Error updating match: {str(e)}")
        raise

def update_match_details_in_db(db, match_data):
    """Update match details including events and statistics"""
    try:
        fixture = match_data['fixture']
        match = db.query(Match).filter_by(api_match_id=fixture['id']).first()
        
        if not match:
            match = update_match_in_db(db, match_data)
        
        # Add events
        if 'events' in match_data:
            for event in match_data['events']:
                event_obj = MatchEvent(
                    match_id=match.id,
                    player_id=event.get('player', {}).get('id'),
                    event_type=event.get('type'),
                    minute=event.get('time', {}).get('elapsed'),
                    details=event.get('detail')
                )
                db.add(event_obj)
        
        return match
    except Exception as e:
        logger.error(f"Error updating match details: {str(e)}")
        raise

def update_team_in_db(db, team_data):
    """Update or create team in database"""
    try:
        team_info = team_data['team']
        team = db.query(Team).filter_by(id=team_info['id']).first()
        
        if not team:
            team = Team(
                id=team_info['id'],
                name=team_info['name'],
                league=team_data.get('league', {}).get('id'),
                logo_url=team_info.get('logo'),
                venue_name=team_data.get('venue', {}).get('name'),
                venue_capacity=team_data.get('venue', {}).get('capacity')
            )
            db.add(team)
        
        return team
    except Exception as e:
        logger.error(f"Error updating team: {str(e)}")
        raise
