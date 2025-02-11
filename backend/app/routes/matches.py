from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from ..database import get_db
from app.api_service.football_api import FootballAPIService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/matches")
football_api = FootballAPIService()

@router.get("/")
async def get_matches(completed: bool = Query(False), db: Session = Depends(get_db)):
    """Get today's matches or completed matches"""
    try:
        matches = await football_api.get_matches(completed=completed)
        return {
            "status": "success",
            "data": matches.get('response', []),
            "message": "Matches retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live")
async def get_live_matches(db: Session = Depends(get_db)):
    """Get currently live matches"""
    try:
        matches = await football_api.get_matches(live=True)
        return {
            "status": "success",
            "data": matches.get('response', []),
            "message": "Live matches retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching live matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team/{team_id}/upcoming")
async def get_upcoming_matches(
    team_id: int, 
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get upcoming matches for a specific team"""
    try:
        response = await football_api.get_upcoming_matches(team_id, limit)
        return {
            "status": "success",
            "data": response.get('response', []),
            "message": f"Upcoming matches for team {team_id} retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error fetching upcoming matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{match_id}")
async def get_match_details(match_id: int):
    """Get detailed information about a specific match"""
    try:
        logger.info(f"Fetching match details for match {match_id}")
        
        response = await football_api.get_match_details(match_id)
        
        if response and 'response' in response:
            return {
                "status": "success",
                "data": response['response'][0],
                "message": "Match details retrieved successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Match details not found")
            
    except Exception as e:
        logger.error(f"Error fetching match details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/league/{league_id}")
async def get_league_matches(league_id: int, db: Session = Depends(get_db)):
    """Hämta matcher för en specifik liga för dagens datum"""
    try:
        matches = await football_api.get_matches()

        league_matches = [m for m in matches.get("response", []) if m["league"]["id"] == league_id]

        return {
            "status": "success",
            "data": league_matches,
            "message": f"Matches for league {league_id} retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

