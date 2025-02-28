from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
from datetime import datetime
import logging
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

def calculate_age(birth_date_str):
    try:
        if not birth_date_str:
            return None
            
        # Parse the birth date string (assuming format: "YYYY-MM-DD")
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        today = datetime.now()
        
        age = today.year - birth_date.year
        
        # Check if birthday has occurred this year
        has_birthday_passed = (
            today.month > birth_date.month or 
            (today.month == birth_date.month and today.day >= birth_date.day)
        )
        
        if not has_birthday_passed:
            age -= 1
            
        return age
    except Exception as e:
        logger.error(f"Error calculating age: {str(e)}")
        return None

def get_current_season():
    current_date = datetime.now()
    # For football seasons that span two years (e.g. 2024/25)
    # If we're between January and July, we're in the latter part of the season
    # If we're between August and December, we're in the early part of the season
    if current_date.month < 8:  # January to July
        return current_date.year - 1  # Return the year the season started
    else:  # August to December
        return current_date.year

@router.get("/")
def get_players(db: Session = Depends(get_db)):
    return {"message": "List of players"}

@router.get("/{team_id}/players/{player_id}")
async def get_player_details(
    response: Response,
    team_id: int = Path(..., description="The team ID"),
    player_id: int = Path(..., description="The player ID"),
):
    try:
        # Set no-cache headers
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        logger.info(f"Fetching detailed stats for player {player_id}")
        
        # Get player info
        player_info = football_api.get_player_info(player_id)
        if not player_info or 'response' not in player_info:
            raise HTTPException(status_code=404, detail="Player not found")
            
        player_details = player_info['response'][0]
        
        # Get current stats including live fixture data
        stats_response = football_api.get_player_statistics(
            player_id=player_id,
            team_id=team_id
        )

        if stats_response and stats_response.get('response'):
            return {
                "status": "success",
                "data": {
                    "player": player_details,
                    "statistics": stats_response['response']
                }
            }

        return {
            "status": "success",
            "data": {
                "player": player_details,
                "statistics": []
            }
        }

    except Exception as e:
        logger.error(f"Error in get_player_details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics/{player_id}")
async def get_player_statistics(
    player_id: int,
    team_id: int = Query(None, description="Optional team ID to filter statistics"),
    season: int = None
):
    try:
        if not season:
            current_season = datetime.now().year
            if datetime.now().month < 8:
                current_season -= 1
            season = current_season

        logger.info(f"Fetching statistics for player {player_id}, season {season}")
        
        stats_response =  football_api.get_player_statistics(
            season=season,
            player_id=player_id,
            team=team_id
        )
        
        if not stats_response or not stats_response.get('response'):
            raise HTTPException(
                status_code=404,
                detail=f"No statistics found for player {player_id}"
            )

        return {
            "status": "success",
            "data": stats_response['response'],
            "message": "Player statistics retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Error fetching player statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{team_id}/players/{player_id}/history")
async def get_player_history(team_id: int, player_id: int):
    try:
        logger.info(f"Fetching historical stats for player {player_id}")
        all_stats = []
        
        current_year = datetime.now().year
        if datetime.now().month < 8:
            current_year -= 1
            
        # Fetch last 5 seasons
        for season in range(current_year - 4, current_year + 1):
            try:
                stats_response = football_api.get_player_statistics(
                    player_id=player_id,
                    season=season
                )
                
                if stats_response and 'response' in stats_response:
                    season_data = {
                        'season': season,
                        'teams': []
                    }
                    
                    # Group stats by team first
                    team_competitions = {}
                    
                    for stat in stats_response['response']:
                        team_id = stat.get('team', {}).get('id')
                        
                        if team_id not in team_competitions:
                            team_competitions[team_id] = []
                        
                        # Add competition stats if there are appearances
                        if stat.get('games', {}).get('appearences', 0) > 0:
                            team_competitions[team_id].append(stat)
                    
                    # Convert team_competitions to array format
                    for team_stats in team_competitions.values():
                        if team_stats:  # Only add if team has stats
                            season_data['teams'].extend(team_stats)
                    
                    if season_data['teams']:  # Only add seasons with data
                        all_stats.append(season_data)
                    
            except Exception as season_error:
                logger.error(f"Error fetching season {season}: {str(season_error)}")
                continue

        # Calculate career summary
        career_summary = calculate_career_summary(all_stats)
        
        return {
            "status": "success",
            "data": {
                "career_summary": career_summary,
                "seasons": all_stats
            }
        }
                
    except Exception as e:
        logger.error(f"Error in get_player_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def calculate_career_summary(all_stats):
    total_appearances = 0
    total_goals = 0
    total_assists = 0
    total_saves = 0
    total_conceded = 0
    total_clean_sheets = 0
    
    for season in all_stats:
        for stat in season['teams']:
            # Add debug logging
            logger.info(f"Processing stat: {stat}")
            total_appearances += stat.get('games', {}).get('appearences', 0)
            total_saves += stat.get('goals', {}).get('saves', 0) or 0  # Handle None values
            total_conceded += stat.get('goals', {}).get('conceded', 0) or 0  # Handle None values
            total_clean_sheets += stat.get('goals', {}).get('clean_sheets', 0) or 0  # Handle None values
            total_goals += stat.get('goals', {}).get('total', 0) or 0
            total_assists += stat.get('goals', {}).get('assists', 0) or 0
    
    # Add debug logging
    logger.info(f"Career summary calculated: saves={total_saves}, conceded={total_conceded}, clean_sheets={total_clean_sheets}")
    
    return {
        "seasons_played": len(all_stats),
        "total_appearances": total_appearances,
        "total_goals": total_goals,
        "total_assists": total_assists,
        "total_saves": total_saves,
        "total_conceded": total_conceded,
        "total_clean_sheets": total_clean_sheets
    } 