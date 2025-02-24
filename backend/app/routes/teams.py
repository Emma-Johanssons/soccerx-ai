from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
from ..services.celery import celery
from ..tasks import fetch_team_statistics
from ..sql_models.models import Team, TeamStatistics
from ..services.data_sync import DataSyncService
import logging
from datetime import datetime, timedelta
import re
from fastapi_cache.decorator import cache
from ..services.data_service import DataService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
try:
    football_api = FootballAPIService()
except ValueError as e:
    logger.error(f"Error initializing FootballAPIService: {e}")
    football_api = None

def fetch_and_store_team(team_id: int, db: Session):
    """Fetch team data from API and store in database"""
    try:
        team_data = football_api.get_team(team_id)
        if not team_data or 'response' not in team_data:
            raise HTTPException(status_code=404, detail="Team not found")
            
        team_info = team_data['response'][0]['team']
        team = Team(
            id=team_info['id'],
            name=team_info['name'],
            logo_url=team_info.get('logo'),
            founded=team_info.get('founded'),
            venue_name=team_info.get('venue', {}).get('name'),
            venue_capacity=team_info.get('venue', {}).get('capacity'),
            last_updated=datetime.utcnow()
        )
        
        db.add(team)
        db.commit()
        db.refresh(team)
        return team
    except Exception as e:
        logger.error(f"Error fetching and storing team: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def get_cached_statistics(team_id: int, db: Session):
    """Get cached team statistics from database"""
    try:
        stats = (
            db.query(TeamStatistics)
            .filter(
                TeamStatistics.team_id == team_id,
                TeamStatistics.last_updated > datetime.utcnow() - timedelta(hours=24)
            )
            .first()
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting cached statistics: {str(e)}")
        return None

@router.get("/")
async def get_teams(db: Session = Depends(get_db)):
    """Get all teams from the database, fetch from API if not found"""
    try:
        # First try to get from database
        teams = db.query(Team).all()
        
        if not teams:
            logger.info("No teams in database, fetching from API")
            if not football_api:
                raise HTTPException(
                    status_code=500,
                    detail="Football API service not properly initialized"
                )
            
            # Trigger async task to fetch and store teams
            task = fetch_team_statistics.delay()
            teams = task.get(timeout=10)  # Wait up to 10 seconds
            
        return {
            "status": "success",
            "data": teams,
            "message": "Teams retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching teams: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching teams: {str(e)}"
        )

@router.get("/{team_id}")
@cache(expire=3600)  # Cache for 1 hour
async def get_team(team_id: int, db: Session = Depends(get_db)):
    data_service = DataService(db)
    try:
        team = await data_service.get_team(team_id)
        return {"status": "success", "data": team}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/matches")
def get_team_matches(
    team_id: int,
    db: Session = Depends(get_db),
    upcoming: bool = Query(True)
):
    """Get team's matches (upcoming or past)"""
    try:
        response = football_api.get_team_matches(
            team_id,
            next=10 if upcoming else None,
            last=10 if not upcoming else None
        )
        
        if not response or 'response' not in response:
            return {
                "status": "success",
                "data": [],
                "message": "No matches found"
            }
            
        return {
            "status": "success",
            "data": response['response'],
            "message": f"Retrieved {len(response['response'])} matches"
        }
    except Exception as e:
        logger.error(f"Error fetching team matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/players")
async def get_team_players(team_id: int):
    try:
        logger.info(f"Fetching players for team {team_id}")
        current_season = datetime.now().year
        if datetime.now().month < 8:
            current_season -= 1

        response =  football_api.get_team_squad(team_id, current_season)
        
        if not response or 'response' not in response:
            logger.error(f"No squad data found for team {team_id}")
            raise HTTPException(status_code=404, detail="Team squad not found")

        squad_data = response['response'][0].get('players', [])
        
        # Log the first player to check the data structure
        if squad_data:
            logger.info(f"Sample player data: {squad_data[0]}")

        formatted_players = [
            {
                'id': player['id'],  # Make sure this matches the API response
                'name': player['name'],
                'age': player.get('age'),
                'number': player.get('number'),
                'position': player.get('position'),
                'photo': f"https://media.api-sports.io/football/players/{player['id']}.png"
            }
            for player in squad_data
        ]

        return {
            "status": "success",
            "data": formatted_players
        }

    except Exception as e:
        logger.error(f"Error fetching team players: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/players/{player_id}")
async def get_team_player(team_id: int, player_id: int):
    try:
        logger.info(f"Fetching player {player_id} details from team {team_id}")
        current_season = datetime.now().year
        if datetime.now().month < 8:
            current_season -= 1

        # First try to get player statistics
        stats_response =  football_api.get_player_statistics(
            season=current_season,
            player_id=player_id
        )
        
        logger.info(f"Stats response received: {bool(stats_response)}")
        
        if stats_response and 'response' in stats_response and stats_response['response']:
            # Filter statistics for the specific team if multiple teams exist
            team_stats = next(
                (stat for stat in stats_response['response'] 
                 if stat['statistics'] and 
                 any(s['team']['id'] == team_id for s in stat['statistics'])),
                stats_response['response'][0]
            )
            
            logger.info("Returning player statistics")
            return {
                "status": "success",
                "data": team_stats
            }
        
        # If no statistics, try to get basic player info from squad
        logger.info("No statistics found, fetching from squad")
        squad_response = football_api.get_team_squad(team_id, current_season)
        
        if squad_response and 'response' in squad_response:
            squad_data = squad_response['response'][0].get('players', [])
            player_info = next((p for p in squad_data if p['id'] == player_id), None)
            
            if player_info:
                logger.info("Found player in squad data")
                return {
                    "status": "success",
                    "data": {
                        "player": player_info,
                        "statistics": []
                    }
                }
        
        logger.error(f"Player {player_id} not found in team {team_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Player {player_id} not found in team {team_id}"
        )

    except Exception as e:
        logger.error(f"Error fetching player details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/players/{player_id}/history")
async def get_player_history(team_id: int, player_id: int):
    try:
        logger.info(f"Fetching historical stats for player {player_id} from team {team_id}")
        
        current_season = datetime.now().year
        if datetime.now().month < 8:
            current_season -= 1
            
        seasons = range(current_season - 4, current_season + 1)
        all_stats = []
        
        for season in seasons:
            try:
                logger.info(f"Fetching stats for season {season}")
                response =  football_api.get_player_statistics(
                    season=season,
                    player_id=player_id
                )
                
                if response and 'response' in response:
                    for stat in response['response']:
                        if 'statistics' in stat:
                            all_stats.extend(stat['statistics'])
                        else:
                            logger.warning(f"Missing 'statistics' in response for season {season}")
                else:
                    logger.warning(f"No response for season {season}")
                    
            except Exception as season_error:
                logger.error(f"Error fetching season {season}: {str(season_error)}")
                continue
        
        if all_stats:
            season_team_stats = {}
            for stat in all_stats:
                try:
                    # Ensure the season is a valid integer
                    season_value = stat['league']['season']
                    if isinstance(season_value, str):
                        # Extract first 4 digits if they exist
                        season_match = re.search(r'\d{4}', str(season_value))
                        if not season_match:
                            logger.warning(f"Invalid season format: {season_value}")
                            continue
                        season = int(season_match.group(0))
                    else:
                        season = int(season_value)
                    team_id = int(stat['team']['id'])
                    key = f"{season}_{team_id}"
                    
                    if key not in season_team_stats:
                        season_team_stats[key] = {
                            'season': season,
                            'team': stat['team'],
                            'league': stat['league'],
                            'games': {
                                'appearences': 0,
                                'minutes': 0,
                                'lineups': 0,
                                'substitute': 0
                            },
                            'goals': {
                                'total': 0,
                                'assists': 0,
                                'saves': 0,
                                'conceded': 0
                            }
                        }
                    
                    current = season_team_stats[key]
                    current['games']['appearences'] += int(stat['games'].get('appearences', 0) or 0)
                    current['games']['minutes'] += int(stat['games'].get('minutes', 0) or 0)
                    current['games']['lineups'] += int(stat['games'].get('lineups', 0) or 0)
                    current['games']['substitute'] += int(stat['games'].get('substitute', 0) or 0)
                    current['goals']['total'] += int(stat['goals'].get('total', 0) or 0)
                    current['goals']['assists'] += int(stat['goals'].get('assists', 0) or 0)
                    current['goals']['saves'] += int(stat['goals'].get('saves', 0) or 0)
                    current['goals']['conceded'] += int(stat['goals'].get('conceded', 0) or 0)
                    
                except KeyError as e:
                    logger.warning(f"Key error processing stat: {str(e)}")
                    continue
            
            career_totals = {
                'seasons_played': len(set(
                    int(re.search(r'\d{4}', str(stat['league']['season'])).group(0))
                    for stat in all_stats 
                    if re.search(r'\d{4}', str(stat['league']['season']))
                )),
                'total_appearances': sum(int(stat['games'].get('appearences', 0) or 0) for stat in all_stats),
                'total_goals': sum(int(stat['goals'].get('total', 0) or 0) for stat in all_stats),
                'total_assists': sum(int(stat['goals'].get('assists', 0) or 0) for stat in all_stats),
                'seasons': [
                    {
                        'season': season,
                        'teams': [
                            stats for stats in season_team_stats.values()
                            if stats['season'] == season
                        ]
                    }
                    for season in sorted(set(
                        int(re.search(r'\d{4}', str(stat['league']['season'])).group(0))
                        for stat in all_stats 
                        if re.search(r'\d{4}', str(stat['league']['season']))
                    ), reverse=True)
                ]
            }
            
            return {
                "status": "success",
                "data": {
                    "career_summary": career_totals,
                    "detailed_history": list(season_team_stats.values())
                }
            }
        
        raise HTTPException(
            status_code=404,
            detail=f"No historical data found for player {player_id}"
        )

    except Exception as e:
        logger.error(f"Error fetching player history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/statistics")
async def get_team_statistics(team_id: int):
    """Get team statistics for the current season"""
    try:
        logger.info(f"Fetching team statistics for team {team_id}")
        current_season = datetime.now().year
        if datetime.now().month < 8:  # If before August, use previous year
            current_season -= 1
            
        logger.info(f"Using season: {current_season}")
        
        # List of major leagues to check
        leagues_to_check = [
            39,  # Premier League
            140, # La Liga
            78,  # Bundesliga
            135, # Serie A
            61,  # Ligue 1
            2,   # Champions League
            3,   # Europa League
            848, # Conference League
            88,  # Eredivisie
            94,  # Primeira Liga
            203, # Super Lig
            71,  # Brasileirao
            128  # Argentine Primera División
        ]
        
        # Try each league until we find valid statistics
        for league_id in leagues_to_check:
            logger.info(f"Checking league {league_id} for team {team_id}")
            
            # Try to get statistics for this league
            response =  football_api.get_team_statistics(team_id, league_id, current_season)
            
            if response and 'response' in response:
                # Check if we have actual statistics (not all zeros)
                fixtures = response['response'].get('fixtures', {})
                if fixtures.get('played', {}).get('total', 0) > 0:
                    logger.info(f"Found valid statistics in league {league_id}")
                    return {
                        "status": "success",
                        "data": response['response'],
                        "message": "Team statistics retrieved successfully"
                    }
        
        # If we get here, no valid statistics were found
        logger.error(f"No valid statistics found for team {team_id} in any league")
        raise HTTPException(status_code=404, detail="No statistics found")
            
    except Exception as e:
        logger.error(f"Error in get_team_statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/live/matches")
@cache(expire=300)  # Cache for 5 minutes
def get_live_matches(db: Session = Depends(get_db)):
    """Get all live matches"""
    try:
        response = football_api.get_matches(date=datetime.now().strftime("%Y-%m-%d"))
        if not response or 'response' not in response:
            return {
                "status": "success",
                "data": [],
                "message": "No live matches found"
            }
            
        # Filter for live matches only
        live_matches = [
            match for match in response['response']
            if match['fixture']['status']['short'] in ['1H', '2H', 'HT']
        ]
        
        return {
            "status": "success",
            "data": live_matches,
            "message": f"Found {len(live_matches)} live matches"
        }
    except Exception as e:
        logger.error(f"Error fetching live matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))