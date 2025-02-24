from fastapi import APIRouter, HTTPException, Depends
from ..api_service.football_api import FootballAPIService
import logging
from sqlalchemy.orm import Session
from datetime import datetime
from app.sql_models.models import Standing
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/{league_id}/{season}")
async def get_standings(league_id: int, season: int, db: Session = Depends(get_db)):
    """Get standings for a specific league and season"""
    logger.info(f"Fetching standings for league {league_id}, season {season}")
    try:
        # First check database
        standings = db.query(Standing)\
            .filter(Standing.league_id == league_id)\
            .filter(Standing.season == season)\
            .all()
            
        # If not in database or data is stale, fetch from API
        if not standings:
            try:
                response = football_api.get_standings(league_id, season)
                if not response or 'response' not in response:
                    raise HTTPException(status_code=404, detail="Standings not found")
                
                # The API response structure might vary, handle empty response
                if not response['response']:
                    return {
                        "status": "success",
                        "data": [],
                        "message": "No standings available"
                    }
                
                standings_data = response['response'][0]['league']['standings']
                if not standings_data:
                    return {
                        "status": "success",
                        "data": [],
                        "message": "No standings available"
                    }
                
                # Flatten standings if they're grouped
                if isinstance(standings_data[0], list):
                    standings_data = standings_data[0]
                
                # Store in database
                for standing in standings_data:
                    standing_obj = Standing(
                        league_id=league_id,
                        team_id=standing['team']['id'],
                        season=season,
                        rank=standing['rank'],
                        points=standing['points'],
                        played=standing['all']['played'],
                        wins=standing['all']['win'],
                        draws=standing['all']['draw'],
                        losses=standing['all']['lose'],
                        goals_for=standing['all']['goals']['for'],
                        goals_against=standing['all']['goals']['against'],
                        goal_difference=standing['goalsDiff'],
                        last_updated=datetime.utcnow()
                    )
                    db.add(standing_obj)
                
                try:
                    db.commit()
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error committing standings: {str(e)}")
                    raise
                
                return {
                    "status": "success",
                    "data": standings_data,
                    "message": "Standings retrieved successfully"
                }
                
            except Exception as e:
                logger.error(f"Error fetching standings: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # If we have data in database, return that
        return {
            "status": "success",
            "data": [s.to_dict() for s in standings],
            "message": "Standings retrieved from database"
        }
        
    except Exception as e:
        logger.error(f"Error getting standings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 