from fastapi import APIRouter, HTTPException
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends
from ..database import get_db
from ..sql_models.models import League, Team

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

MAJOR_LEAGUES = {
    "39": "Premier League",
    "140": "La Liga",
    "135": "Serie A",
    "78": "Bundesliga",
    "61": "Ligue 1",
}

@router.get("/")
async def search(q: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Searching database for: {q}")
        results = []
        
        # Search in database first
        leagues = db.query(League).filter(League.name.ilike(f"%{q}%")).all()
        teams = db.query(Team).filter(Team.name.ilike(f"%{q}%")).all()
        
        logger.info(f"Found {len(leagues)} leagues and {len(teams)} teams in database")
        
        # Format results
        for league in leagues:
            try:
                results.append({
                    'id': league.id,
                    'name': league.name,
                    'type': 'league',
                    'logo': league.logo,
                    'country': league.country.country_name if league.country else None
                })
            except AttributeError as e:
                logger.error(f"Error formatting league {league.id}: {str(e)}")
                
        for team in teams:
            try:
                results.append({
                    'id': team.id,
                    'name': team.name,
                    'type': 'team',
                    'logo': team.logo_url,
                    'country': team.country.country_name if team.country else None
                })
            except AttributeError as e:
                logger.error(f"Error formatting team {team.id}: {str(e)}")
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 