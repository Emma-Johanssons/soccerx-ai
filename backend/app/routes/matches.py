from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime, timedelta
import requests
from ..sql_models.models import Match, MatchEvent, Player, Team
from ..api_service.football_api import FootballAPIService
from typing import Optional, Dict

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/test-api")
async def test_api():
    """Test endpoint to verify API connectivity"""
    return football_api.test_api()

@router.get("/")
def get_matches(
    completed: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get matches for today"""
    try:
        logger.info(f"Fetching {'completed' if completed else 'upcoming'} matches")
        
        # Get today's date with correct year
        today = datetime.now().replace(year=2025).strftime('%Y-%m-%d')
        logger.info(f"Fetching matches for date: {today}")
        
        # Call API
        response = football_api.get_matches(date=today)
        logger.info(f"API Response received: {response}")
        
        if not response or 'response' not in response:
            logger.warning("No matches found or invalid response")
            return {
                "status": "success",
                "data": [],
                "message": "No matches found"
            }
            
        matches = response['response']
        
        # Filter and format matches
        filtered_matches = []
        for match in matches:
            status = match['fixture']['status']['short']
            is_completed = status in ['FT', 'AET', 'PEN']
            
            if completed == is_completed:  # Only include matches that match our completed parameter
                formatted_match = {
                    'fixture': {
                        'id': match['fixture']['id'],
                        'date': match['fixture']['date'],
                        'timestamp': match['fixture']['timestamp'],
                        'status': {
                            'long': match['fixture']['status']['long'],
                            'short': status,
                            'elapsed': match['fixture']['status'].get('elapsed')
                        }
                    },
                    'league': {
                        'id': match['league']['id'],
                        'name': match['league']['name'],
                        'logo': match['league'].get('logo')
                    },
                    'teams': {
                        'home': {
                            'id': match['teams']['home']['id'],
                            'name': match['teams']['home']['name'],
                            'logo': match['teams']['home'].get('logo')
                        },
                        'away': {
                            'id': match['teams']['away']['id'],
                            'name': match['teams']['away']['name'],
                            'logo': match['teams']['away'].get('logo')
                        }
                    },
                    'goals': {
                        'home': match['goals']['home'],
                        'away': match['goals']['away']
                    }
                }
                filtered_matches.append(formatted_match)
            
        return {
            "status": "success",
            "data": filtered_matches,
            "message": f"Successfully retrieved {len(filtered_matches)} matches"
        }
            
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching matches: {str(e)}"
        )

@router.get("/league/{league_id}")
async def get_league_matches(league_id: int, db: Session = Depends(get_db)):
    """Get matches for a specific league"""
    try:
        url = f"{football_api.base_url}/fixtures"
        params = {
            'league': league_id,
            'season': '2023',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        response = requests.get(
            url,
            headers=football_api.headers,
            params=params
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch league matches"
            )
            
        data = response.json()
        logger.info(f"League {league_id} matches: {data}")
        
        return {
            "status": "success",
            "data": data.get('response', []),
            "message": f"Matches for league {league_id} retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching league matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def ensure_player_exists(db: Session, player_data: Dict, team_id: int) -> Optional[int]:
    """Ensure player exists in database, create if not exists"""
    if not player_data or 'id' not in player_data:
        return None
        
    player_id = player_data['id']
    player = db.query(Player).filter(Player.id == player_id).first()
    
    if not player:
        player = Player(
            id=player_id,
            name=player_data.get('name'),
            team_id=team_id,
            position=player_data.get('position'),
            jersey_number=player_data.get('number'),
            photo_url=player_data.get('photo')
        )
        try:
            db.add(player)
            db.flush()  # Flush but don't commit yet
            logger.info(f"Created new player: {player_id} - {player_data.get('name')}")
        except Exception as e:
            logger.error(f"Error creating player {player_id}: {str(e)}")
            return None
            
    return player_id

@router.get("/{match_id}")
async def get_match_details(match_id: int, db: Session = Depends(get_db)):
    """Get detailed information for a specific match"""
    try:
        match = db.query(Match).filter(Match.api_match_id == match_id).first()
        
        if not match or match.is_stale():
            try:
                logger.info(f"Fetching match {match_id} from API")
                response = await football_api.get_match(match_id)
                
                if not response or not response.get('response'):
                    raise HTTPException(status_code=404, detail="Match not found in API")
                
                match_data = response['response'][0]
                
                # Parse the date
                match_date = None
                if isinstance(match_data['fixture']['date'], str):
                    try:
                        match_date = datetime.fromisoformat(match_data['fixture']['date'].replace('Z', '+00:00'))
                    except ValueError:
                        logger.error(f"Could not parse date: {match_data['fixture']['date']}")
                
                # Create or update match
                if not match:
                    match = Match(
                        api_match_id=match_id,
                        date=match_date,
                        stadium=match_data['fixture']['venue']['name'],
                        referee=match_data['fixture']['referee'],
                        home_team_id=match_data['teams']['home']['id'],
                        away_team_id=match_data['teams']['away']['id'],
                        score_home=match_data['goals']['home'],
                        score_away=match_data['goals']['away'],
                        league_id=match_data['league']['id'],
                        last_updated=datetime.utcnow()
                    )
                    db.add(match)
                    db.flush()  # Get the match ID without committing
                
                # Update events if they exist
                if 'events' in match_data:
                    logger.info(f"Processing {len(match_data['events'])} events for match {match_id}")
                    # Clear existing events for this match
                    if match.id:
                        db.query(MatchEvent).filter(MatchEvent.match_id == match.id).delete()
                    
                    for event_data in match_data['events']:
                        try:
                            logger.info(f"Processing event: {event_data}")
                            # Ensure players exist in database
                            player_id = await ensure_player_exists(
                                db, 
                                event_data.get('player'), 
                                event_data['team']['id']
                            )
                            assist_player_id = await ensure_player_exists(
                                db, 
                                event_data.get('assist'), 
                                event_data['team']['id']
                            )
                            
                            event = MatchEvent(
                                match_id=match.id,
                                team_id=event_data['team']['id'],
                                player_id=player_id,
                                assist_player_id=assist_player_id,
                                type=event_data['type'],
                                time=event_data['time']['elapsed'],
                                details=event_data.get('detail')
                            )
                            db.add(event)
                            logger.info(f"Added event: {event.type} at {event.time}'")
                        except Exception as e:
                            logger.error(f"Error processing event: {str(e)}, event data: {event_data}")
                            continue
                
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error committing changes: {str(e)}")
                    raise
                    
            except Exception as e:
                logger.error(f"Error fetching match from API: {str(e)}")
                if not match:
                    raise HTTPException(status_code=404, detail="Match not found")
        
        # Return match data
        return {
            "status": "success",
            "data": {
                "fixture": {
                    "id": match.api_match_id,
                    "date": match.date.isoformat() if isinstance(match.date, datetime) else match.date,
                    "venue": {"name": match.stadium},
                    "referee": match.referee,
                    "status": {"short": match.status.code if match.status else None}
                },
                "league": {
                    "id": match.league_id,
                    "name": match.league.name if match.league else None
                },
                "teams": {
                    "home": {
                        "id": match.home_team_id,
                        "name": match.home_team.name if match.home_team else None,
                        "logo": match.home_team.logo_url if match.home_team else None
                    },
                    "away": {
                        "id": match.away_team_id,
                        "name": match.away_team.name if match.away_team else None,
                        "logo": match.away_team.logo_url if match.away_team else None
                    }
                },
                "goals": {
                    "home": match.score_home,
                    "away": match.score_away
                },
                "events": [
                    {
                        "time": {"elapsed": event.time},
                        "team": {
                            "id": event.team_id,
                            "name": event.team.name if event.team else None
                        },
                        "player": {
                            "id": event.player_id,
                            "name": event.player.name if event.player else None
                        } if event.player_id else None,
                        "assist": {
                            "id": event.assist_player_id,
                            "name": event.assist_player.name if event.assist_player else None
                        } if event.assist_player_id else None,
                        "type": event.type,
                        "detail": event.details
                    } for event in match.events
                ] if match.events else []
            },
            "message": "Match details retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error in get_match_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live")
async def get_live_matches(db: Session = Depends(get_db)):
    try:
        # Get live matches from the football API
        matches = football_api.get_matches(live=True)
        return {
            "status": "success",
            "data": matches.get('response', []),
            "message": "Live matches retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching live matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/upcoming")
def get_upcoming_matches(team_id: int, db: Session = Depends(get_db)):
    return {"message": f"Upcoming matches for team {team_id}"}

def update_match_in_db(db: Session, match_data: dict) -> Match:
    """Update or create match in database"""
    try:
        fixture = match_data['fixture']
        match = db.query(Match).filter(Match.api_match_id == fixture['id']).first()
        
        match_dict = {
            'api_match_id': fixture['id'],
            'date': datetime.fromtimestamp(fixture['timestamp']),
            'stadium': fixture['venue'].get('name'),
            'referee': fixture.get('referee'),
            'home_team_id': match_data['teams']['home']['id'],
            'away_team_id': match_data['teams']['away']['id'],
            'league_id': match_data['league']['id'],
            'match_status_id': get_status_id(fixture['status']['short']),
            'score_home': match_data['goals']['home'],
            'score_away': match_data['goals']['away'],
            'last_updated': datetime.utcnow()
        }
        
        if not match:
            match = Match(**match_dict)
            db.add(match)
            db.commit()
            db.refresh(match)
        else:
            for key, value in match_dict.items():
                setattr(match, key, value)
            db.commit()
        
        # Add events if available
        if 'events' in match_data and match_data['events']:
            # Clear existing events
            db.query(MatchEvent).filter(MatchEvent.match_id == match.id).delete()
            db.commit()
            
            for event in match_data['events']:
                try:
                    event_obj = MatchEvent(
                        match_id=match.id,
                        team_id=event['team']['id'],
                        player_id=event.get('player', {}).get('id'),
                        type=event['type'],
                        time=event['time']['elapsed'],
                        details=event.get('detail')
                    )
                    db.add(event_obj)
                except Exception as e:
                    logger.error(f"Error creating event: {str(e)}, event data: {event}")
                    continue
            
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Error committing events: {str(e)}")
                db.rollback()
        
        db.refresh(match)
        return match
        
    except Exception as e:
        logger.error(f"Error updating match in database: {str(e)}")
        db.rollback()
        raise

def get_status_id(status_code: str) -> int:
    """Map status code to status ID"""
    status_map = {
        'NS': 1,  # Not Started
        '1H': 2,  # First Half
        'HT': 3,  # Half Time
        '2H': 4,  # Second Half
        'ET': 5,  # Extra Time
        'P': 6,   # Penalty
        'FT': 7,  # Full Time
        'AET': 8, # After Extra Time
        'PEN': 9, # Penalties
        'BT': 10, # Break Time
        'SUSP': 11, # Suspended
        'INT': 12, # Interrupted
        'PST': 13, # Postponed
        'CANC': 14, # Cancelled
        'ABD': 15, # Abandoned
        'AWD': 16, # Technical Loss
        'WO': 17,  # Walk Over
        'LIVE': 18 # Live
    }
    return status_map.get(status_code, 1)  # Default to Not Started if unknown 