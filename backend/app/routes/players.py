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
        
        # Get player statistics first
        stats_response = await football_api.get_player_statistics(
            player_id=player_id,
            season=current_season
        )
        
        logger.info(f"Stats response: {json.dumps(stats_response, indent=2) if stats_response else 'None'}")

        if stats_response and stats_response.get('response'):
            return {
                "status": "success",
                "data": stats_response['response'][0]
            }

        # If no statistics found, get basic player info from squad
        squad_response = await football_api.get_team_squad(team_id, current_season)
        if not squad_response or 'response' not in squad_response:
            logger.error(f"Failed to get squad data for team {team_id}")
            raise HTTPException(status_code=404, detail="Team not found")

        squad_data = squad_response['response'][0].get('players', [])
        player_info = next((p for p in squad_data if p['id'] == player_id), None)

        if not player_info:
            logger.error(f"Player {player_id} not found in team {team_id}")
            raise HTTPException(status_code=404, detail="Player not found in team")

        return {
            "status": "success",
            "data": {
                "player": player_info,
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
        
        stats_response = await football_api.get_player_statistics(
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