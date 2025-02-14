from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime
import requests

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/test-api")
async def test_api():
    """Test endpoint to verify API connectivity"""
    return await football_api.test_api()

@router.get("/")
async def get_matches(completed: bool = False, db: Session = Depends(get_db)):
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

@router.get("/live")
async def get_live_matches(db: Session = Depends(get_db)):
    try:
        # Get live matches from the football API
        matches = await football_api.get_matches(live=True)
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