from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
from ..services.celery import celery
from ..tasks import fetch_team_statistics
from ..sql_models.models import Team, TeamStatistics, Player, Position
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
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Get team details"""
    try:
        # First try to get from database
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            # If not in database, fetch from API and save
            team_data = football_api.get_team(team_id)
            if team_data and team_data.get('response'):
                team_info = team_data['response'][0]['team']
                venue_info = team_data['response'][0].get('venue', {})
                try:
                    team = Team(
                        id=team_id,
                        name=team_info.get('name'),
                        code=team_info.get('code'),
                        logo_url=team_info.get('logo'),
                        founded=team_info.get('founded'),
                        venue_name=venue_info.get('name'),
                        venue_capacity=venue_info.get('capacity'),
                        country_id=None,  # We'll need to handle this separately
                        league=None,  # We'll need to handle this separately
                        last_updated=datetime.utcnow()
                    )
                    db.add(team)
                    db.commit()
                    logger.info(f"Created new team: {team_id} - {team_info.get('name')}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error creating team {team_id}: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error creating team: {str(e)}")
        
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
            
        # Return team data as a dictionary
        return {
            "status": "success",
            "data": {
                "team": {
                    "id": team.id,
                    "name": team.name,
                    "code": team.code,
                    "logo": team.logo_url,
                    "venue": {
                        "name": team.venue_name,
                        "capacity": team.venue_capacity
                    } if team.venue_name else None,
                    "founded": team.founded,
                    "country": team.country.country_name if team.country else None,
                    "league": team.league
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team data: {str(e)}")
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
def get_team_players(team_id: int, db: Session = Depends(get_db)):
    """Get players for a specific team"""
    try:
        # First try to get from database
        players = db.query(Player).filter(Player.team_id == team_id).all()
        
        if not players:
            # If not in database, fetch from API and save
            players_data = football_api.get_team_players(team_id)
            if players_data and players_data.get('response'):
                players = []
                # Get or create default positions first
                position_map = {
                    "Goalkeeper": db.query(Position).filter(Position.name == "Goalkeeper").first(),
                    "Defender": db.query(Position).filter(Position.name == "Defender").first(),
                    "Midfielder": db.query(Position).filter(Position.name == "Midfielder").first(),
                    "Attacker": db.query(Position).filter(Position.name == "Attacker").first()
                }
                
                # Create any missing positions
                for pos_name, pos in position_map.items():
                    if not pos:
                        position_map[pos_name] = Position(name=pos_name)
                        db.add(position_map[pos_name])
                
                try:
                    db.flush()  # Ensure positions are created and have IDs
                except Exception as e:
                    logger.error(f"Error creating positions: {str(e)}")
                    db.rollback()
                    raise HTTPException(status_code=500, detail="Error creating positions")

                # Now create players with proper position references
                for player_info in players_data['response'][0]['players']:
                    try:
                        position_name = player_info.get('position')
                        position = position_map.get(position_name)
                        
                        if not position:
                            logger.warning(f"Unknown position {position_name} for player {player_info['name']}")
                            continue
                            
                        player = Player(
                            id=player_info['id'],
                            name=player_info['name'],
                            team_id=team_id,
                            position_id=position.id,
                            birth_date=None  # We'll handle this separately if needed
                        )
                        db.add(player)
                        players.append(player)
                        
                    except Exception as e:
                        logger.error(f"Error creating player {player_info.get('name')}: {str(e)}")
                        continue
                
                try:
                    db.commit()
                    logger.info(f"Created {len(players)} players for team {team_id}")
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error committing players for team {team_id}: {str(e)}")
                    raise HTTPException(status_code=500, detail=f"Error saving players: {str(e)}")
        
        # Return players data as a list of dictionaries
        return {
            "status": "success",
            "data": {
                "players": [{
                    "id": player.id,
                    "name": player.name,
                    "position": player.position.name if player.position else None,
                    "birth_date": player.birth_date.isoformat() if player.birth_date else None
                } for player in players]
            }
        }
        
    except HTTPException:
        raise
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
    try:
        logger.info(f"Fetching team statistics for team {team_id}")
        current_season = datetime.now().year
        if datetime.now().month < 8:
            current_season -= 1

        # Get team info first
        team_info = football_api.get_team_info(team_id)
        if not team_info or 'response' not in team_info or not team_info['response']:
            raise HTTPException(status_code=404, detail="Team not found")
            
        team_data = team_info['response'][0]
        team_country = team_data['team']['country']
        
        # Get coach info - get the current coach
        coach_response = football_api.get_team_coach(team_id)
        coach_info = None
        if coach_response and 'response' in coach_response and coach_response['response']:
            current_time = datetime.now()
            latest_coach = None
            latest_start_date = None

            for coach in coach_response['response']:
                if 'career' in coach:
                    for stint in coach['career']:
                        if stint['team']['id'] == team_id:
                            start_date = datetime.strptime(stint['start'], '%Y-%m-%d')
                            # Check if this is a more recent appointment
                            if (latest_start_date is None or start_date > latest_start_date):
                                # For current coaches, 'end' should be None
                                if stint['end'] is None:
                                    latest_start_date = start_date
                                    latest_coach = coach

            if latest_coach:
                coach_info = {
                    'name': latest_coach['name'],
                    'age': latest_coach['age'],
                    'nationality': latest_coach['nationality'],
                    'photo': latest_coach['photo']
                }
                logger.info(f"Found current coach: {latest_coach['name']} (started: {latest_start_date})")

        # Get team's matches to identify all competitions
        matches = football_api.get_team_matches(team_id, current_season)
        leagues = {}
        domestic_league = None
        
        if matches and 'response' in matches:
            # Collect all unique leagues the team plays in
            for match in matches['response']:
                league = match['league']
                league_id = league['id']
                
                if league_id not in leagues:
                    leagues[league_id] = league
                    # Identify domestic league based on country match and type
                    if (league['country'] == team_country and 
                        league.get('type', '').lower() in ['league', 'first division']):
                        domestic_league = league

        # Initialize overall stats
        overall_stats = {
            "team": {
                "id": team_data['team']['id'],
                "name": team_data['team']['name'],
                "country": team_data['team']['country'],
                "founded": team_data['team']['founded'],
                "logo": team_data['team']['logo'],
                "coach": coach_info,
                "venue": team_data['venue']
            },
            "fixtures": {
                "played": {"total": 0},
                "wins": {"total": 0},
                "draws": {"total": 0},
                "loses": {"total": 0}
            },
            "goals": {
                "for": {"total": {"total": 0}},
                "against": {"total": {"total": 0}}
            },
            "clean_sheet": {"total": 0},
            "league": domestic_league or next(iter(leagues.values())) if leagues else None  # Fallback to first league if no domestic league found
        }

        # Get statistics for each league
        all_stats = []
        for league_id, league_info in leagues.items():
            league_stats = football_api.get_team_statistics(team_id, league_id, current_season)
            if league_stats and 'response' in league_stats:
                stats = league_stats['response']
                stats['league'] = league_info  # Add league information to stats
                all_stats.append(stats)
                
                # Sum up statistics for overall view
                overall_stats['fixtures']['played']['total'] += stats.get('fixtures', {}).get('played', {}).get('total', 0) or 0
                overall_stats['fixtures']['wins']['total'] += stats.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                overall_stats['fixtures']['draws']['total'] += stats.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                overall_stats['fixtures']['loses']['total'] += stats.get('fixtures', {}).get('loses', {}).get('total', 0) or 0
                overall_stats['goals']['for']['total']['total'] += stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0) or 0
                overall_stats['goals']['against']['total']['total'] += stats.get('goals', {}).get('against', {}).get('total', {}).get('total', 0) or 0
                overall_stats['clean_sheet']['total'] += stats.get('clean_sheet', {}).get('total', 0) or 0
            
        logger.info(f"Found statistics for {len(all_stats)} leagues")
        
        # Get form from matches
        form = []
        if matches and 'response' in matches:
            sorted_matches = sorted(
                [m for m in matches['response'] if m['fixture']['status']['short'] == 'FT'],
                key=lambda x: x['fixture']['date'],
                reverse=True
            )[:5]
            
            for match in sorted_matches:
                if match['teams']['home']['id'] == team_id:
                    if match['goals']['home'] > match['goals']['away']:
                        form.append('W')
                    elif match['goals']['home'] < match['goals']['away']:
                        form.append('L')
                    else:
                        form.append('D')
                else:
                    if match['goals']['away'] > match['goals']['home']:
                        form.append('W')
                    elif match['goals']['away'] < match['goals']['home']:
                        form.append('L')
                    else:
                        form.append('D')
        
        logger.info(f"Team form: {form}")
        
        return {
            "status": "success",
            "data": {
                "overall": overall_stats,
                "by_league": all_stats,
                "form": form
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_team_statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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