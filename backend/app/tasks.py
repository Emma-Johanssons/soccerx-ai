from celery import shared_task
from app.database import SessionLocal
from app.api_service.football_api import FootballAPIService
from datetime import datetime, timedelta
import logging
from app.sql_models.models import Match, Team, MatchEvent, Player, League, Standing, TeamStatistics, PlayerStatistics, MatchStatistic
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
    """Weekly sync of static data"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_teams()
        sync_service.sync_leagues()
        logger.info("Static data sync completed")
    finally:
        db.close()

@shared_task
def sync_daily_data():
    """12-hour sync of standings and statistics"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_standings()
        logger.info("Daily data sync completed")
    finally:
        db.close()

@shared_task
def sync_todays_matches():
    """Fetch and store today's matches (upcoming and live)"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        today = datetime.now().date()
        
        # Fetch today's matches
        matches = football_api.get_matches(date=today)
        
        for match_data in matches.get('response', []):
            fixture = match_data['fixture']
            match = Match(
                id=fixture['id'],
                home_team_id=fixture['teams']['home']['id'],
                away_team_id=fixture['teams']['away']['id'],
                start_time=fixture['date'],
                status=fixture['status']['short'],
                home_score=fixture['goals']['home'],
                away_score=fixture['goals']['away'],
                league_id=fixture['league']['id'],
                last_updated=datetime.utcnow()
            )
            
            # Update or create match
            existing_match = db.query(Match).filter(Match.id == match.id).first()
            if existing_match:
                for key, value in match.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing_match, key, value)
            else:
                db.add(match)
                
        db.commit()
        logger.info("Today's matches synced successfully")
    except Exception as e:
        logger.error(f"Error syncing today's matches: {str(e)}")
        db.rollback()
    finally:
        db.close()

@shared_task
def sync_completed_matches():
    """Sync completed matches with full details"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        yesterday = datetime.now() - timedelta(days=1)
        
        # Get completed matches
        completed_matches = db.query(Match).filter(
            Match.start_time >= yesterday,
            Match.status.in_(['FT', 'AET', 'PEN'])
        ).all()
        
        for match in completed_matches:
            # Update match statistics
            stats = football_api.get_match_statistics(match.id)
            if stats:
                # Update match statistics logic here
                pass
            
            # Get and store match events
            events = football_api.get_match_events(match.id)
            if events:
                for event_data in events.get('response', []):
                    event = MatchEvent(
                        match_id=match.id,
                        event_time=event_data['time']['elapsed'],
                        event_type=event_data['type'],
                        player_id=event_data['player']['id'],
                        team_id=event_data['team']['id'],
                        details=event_data['detail']
                    )
                    db.add(event)
            
            # Get and store lineups
            lineups = football_api.get_match_lineups(match.id)
            if lineups:
                # Store lineup data logic here
                pass
                
            match.last_updated = datetime.utcnow()
            
        db.commit()
        logger.info("Completed matches synced successfully")
    except Exception as e:
        logger.error(f"Error syncing completed matches: {str(e)}")
        db.rollback()
    finally:
        db.close()

@shared_task
def sync_live_matches():
    """Update live match data every minute"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        
        # Get live matches
        live_matches = football_api.get_matches(live=True)
        
        for match_data in live_matches.get('response', []):
            fixture = match_data['fixture']
            
            # Update match
            match = db.query(Match).filter(Match.id == fixture['id']).first()
            if match:
                match.status = fixture['status']['short']
                match.home_score = fixture['goals']['home']
                match.away_score = fixture['goals']['away']
                match.last_updated = datetime.utcnow()
                
                # Get and store latest match statistics
                stats = football_api.get_match_statistics(match.id)
                if stats:
                    for stat_data in stats.get('response', []):
                        match_stat = MatchStatistic(
                            match_id=match.id,
                            team_id=stat_data['team']['id'],
                            shots_on_goal=stat_data.get('shots', {}).get('on'),
                            shots_off_goal=stat_data.get('shots', {}).get('off'),
                            total_shots=stat_data.get('shots', {}).get('total'),
                            possession=stat_data.get('possession'),
                            passes=stat_data.get('passes', {}).get('total'),
                            pass_accuracy=stat_data.get('passes', {}).get('accuracy'),
                            fouls=stat_data.get('fouls'),
                            yellow_cards=stat_data.get('cards', {}).get('yellow'),
                            red_cards=stat_data.get('cards', {}).get('red'),
                            offsides=stat_data.get('offsides'),
                            corners=stat_data.get('corners')
                        )
                        db.add(match_stat)
                
        db.commit()
        logger.info("Live matches updated successfully")
    except Exception as e:
        logger.error(f"Error updating live matches: {str(e)}")
        db.rollback()
    finally:
        db.close()

@shared_task
def sync_team_statistics(team_id: int):
    """Background task for team statistics"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.fetch_and_store_team_statistics(team_id)
        logger.info(f"Team statistics synced for team {team_id}")
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
def sync_daily_matches():
    """Sync completed matches from yesterday and upcoming matches"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Yesterday's completed matches
        yesterday = datetime.now() - timedelta(days=1)
        completed_matches = football_api.get_matches(date=yesterday)
        for match in completed_matches.get('response', []):
            sync_service.store_match(match)
            
        # Upcoming matches for next 7 days
        for days in range(7):
            date = datetime.now() + timedelta(days=days)
            upcoming_matches = football_api.get_matches(date=date)
            for match in upcoming_matches.get('response', []):
                sync_service.store_match(match)
                
        logger.info("Daily matches sync completed")
    finally:
        db.close()

@shared_task
def sync_player_statistics():
    """Sync player statistics daily"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Get all players from database
        players = db.query(Player).all()
        for player in players:
            # Get and store player statistics
            stats = football_api.get_player_statistics(player.id)
            sync_service.store_player_statistics(player.id, stats)
            
        logger.info("Player statistics sync completed")
    finally:
        db.close()

@shared_task
def sync_match_statistics():
    """Sync match statistics for completed matches"""
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        
        # Get yesterday's matches
        yesterday = datetime.now() - timedelta(days=1)
        matches = football_api.get_matches(date=yesterday)
        
        for match in matches.get('response', []):
            match_id = match['fixture']['id']
            # Get and store match statistics
            stats = football_api.get_match_statistics(match_id)
            sync_service.store_match_statistics(match_id, stats)
            
        logger.info("Match statistics sync completed")
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

@shared_task
def sync_league_data():
    """Sync league data including standings"""
    db = SessionLocal()
    api = FootballAPIService()
    
    try:
        # Get all leagues from database
        leagues = db.query(League).all()
        
        for league in leagues:
            # Update league info
            league_data = api.get_leagues(league.id)
            if league_data:
                # Update league attributes
                for key, value in league_data.items():
                    setattr(league, key, value)
                
            # Update standings
            standings_data = api.get_standings(league.id, datetime.now().year)
            if standings_data:
                # Clear old standings
                db.query(Standing).filter_by(league_id=league.id).delete()
                
                # Insert new standings
                for standing in standings_data:
                    new_standing = Standing(**standing)
                    db.add(new_standing)
            
            league.last_updated = datetime.utcnow()
        
        db.commit()
    finally:
        db.close()

@shared_task
def sync_team_statistics():
    """Sync team statistics"""
    db = SessionLocal()
    api = FootballAPIService()
    
    try:
        teams = db.query(Team).all()
        current_season = datetime.now().year
        
        for team in teams:
            stats_data = api.get_team_statistics(team.id, current_season)
            if stats_data:
                # Update or create team statistics
                stats = db.query(TeamStatistics).filter_by(
                    team_id=team.id,
                    season=current_season
                ).first()
                
                if not stats:
                    stats = TeamStatistics(team_id=team.id, season=current_season)
                    db.add(stats)
                
                for key, value in stats_data.items():
                    setattr(stats, key, value)
                
                stats.last_updated = datetime.utcnow()
        
        db.commit()
    finally:
        db.close()

@shared_task
def sync_player_statistics():
    """Sync player statistics"""
    db = SessionLocal()
    api = FootballAPIService()
    
    try:
        players = db.query(Player).all()
        current_season = datetime.now().year
        
        for player in players:
            stats_data = api.get_player_statistics(player.id, current_season)
            if stats_data:
                # Update or create player statistics
                stats = db.query(PlayerStatistics).filter_by(
                    player_id=player.id,
                    season=current_season
                ).first()
                
                if not stats:
                    stats = PlayerStatistics(player_id=player.id, season=current_season)
                    db.add(stats)
                
                for key, value in stats_data.items():
                    setattr(stats, key, value)
                
                stats.last_updated = datetime.utcnow()
        
        db.commit()
    finally:
        db.close()
