from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
from datetime import datetime
import logging
from typing import Optional
import json

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/")
def get_players(db: Session = Depends(get_db)):
    return {"message": "List of players"}

@router.get("/{player_id}")
async def get_player_details(
    player_id: int,
    team_id: int = Query(..., description="The team ID is required")
):
    try:
        current_season = datetime.now().year
        if datetime.now().month < 8:
            current_season -= 1

        logger.info(f"Attempting to fetch detailed stats for player {player_id}")
        
        # Get player information first to ensure correct age
        player_info = football_api.get_player_info(player_id)
        if not player_info or 'response' not in player_info:
            logger.error(f"Failed to get player info for player {player_id}")
            raise HTTPException(status_code=404, detail="Player not found")
            
        # Extract player details including correct age
        player_details = player_info['response'][0]
        
        # Get player statistics for both current and previous season to catch transfers
        stats_response = football_api.get_player_statistics(
            player_id=player_id,
            season=current_season
        )
        
        # Also get previous season's stats if we're after August
        if datetime.now().month >= 8:
            prev_stats_response = football_api.get_player_statistics(
                player_id=player_id,
                season=current_season - 1
            )
            
            # If we have previous season stats, check for matches after August
            if prev_stats_response and prev_stats_response.get('response'):
                for stat in prev_stats_response['response']:
                    if 'statistics' in stat:
                        for match_stat in stat['statistics']:
                            # Only include stats from matches after August
                            match_date = datetime.strptime(match_stat.get('date', ''), '%Y-%m-%d')
                            if match_date.month >= 8:
                                if not stats_response:
                                    stats_response = {'response': []}
                                stats_response['response'].append(stat)

        if stats_response and stats_response.get('response'):
            all_stats = stats_response['response']
            
            if len(all_stats) > 1:
                logger.info(f"Found multiple team statistics for player {player_id}")
                combined_stats = all_stats[0].copy()
                combined_stats['player'] = player_details  # Use correct player details
                
                for stat in all_stats[1:]:
                    for key in combined_stats.get('games', {}):
                        if isinstance(combined_stats['games'][key], (int, float)):
                            combined_stats['games'][key] = (combined_stats['games'].get(key, 0) or 0) + (stat['games'].get(key, 0) or 0)
                    
                    for key in combined_stats.get('goals', {}):
                        if isinstance(combined_stats['goals'][key], (int, float)):
                            combined_stats['goals'][key] = (combined_stats['goals'].get(key, 0) or 0) + (stat['goals'].get(key, 0) or 0)
                    
                    if 'competitions' not in combined_stats:
                        combined_stats['competitions'] = []
                    
                    if 'league' in stat:
                        combined_stats['competitions'].append({
                            'league': stat['league'],
                            'team': stat['team'],
                            'games': stat['games'],
                            'goals': stat['goals']
                        })
                
                return {
                    "status": "success",
                    "data": combined_stats
                }
            
            # If single team stats, still use correct player details
            all_stats[0]['player'] = player_details
            return {
                "status": "success",
                "data": all_stats[0]
            }

        # If no statistics found, return basic player info
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