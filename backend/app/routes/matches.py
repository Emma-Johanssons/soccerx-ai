from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from app.api_service.football_api import FootballAPIService

router = APIRouter()
football_api = FootballAPIService()

@router.get("/matches")
async def get_matches(completed: bool = Query(False), db: Session = Depends(get_db)):
    """Hämta dagens matcher eller completed matcher"""
    try:
        matches = await football_api.get_matches(completed=completed)
        return {
            "status": "success",
            "data": matches.get('response', []),
            "message": "Matches retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
