from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..sql_models.models import League, Team, Standing
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/")
async def get_leagues():
    try:
        logger.info("Starting leagues fetch request")
        response =  football_api.get_leagues()
        
        logger.info(f"Raw API response received: {response}")
        
        if response and 'response' in response:
            leagues = response['response']
            logger.info(f"Found {len(leagues)} leagues")
            
            # Format the leagues data
            formatted_leagues = []
            for league in leagues:
                if league.get('league'):
                    formatted_leagues.append({
                        'league': {
                            'id': league['league']['id'],
                            'name': league['league']['name'],
                            'type': league['league']['type'],
                            'logo': league['league'].get('logo'),
                            'country': league['country']['name']
                        }
                    })
            
            logger.info(f"Formatted {len(formatted_leagues)} leagues")
            
            return {
                "status": "success",
                "response": formatted_leagues,
                "message": f"Successfully retrieved {len(formatted_leagues)} leagues"
            }
        else:
            logger.error("No 'response' field in API response")
            raise HTTPException(status_code=404, detail="No leagues found")
            
    except Exception as e:
        logger.error(f"Error fetching leagues: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching leagues: {str(e)}"
        )

@router.get("/{league_id}")
async def get_league(league_id: int, db: Session = Depends(get_db)):
    try:
        # First try to get from database
        league = db.query(League).filter(League.id == league_id).first()
        
        if league and (datetime.utcnow() - league.last_updated).days < 1:
            # Get standings from database if data is fresh
            standings = db.query(Standing).filter(
                Standing.league_id == league_id
            ).all()
            
            return {
                "status": "success",
                "data": {
                    "league": league,
                    "standings": standings
                }
            }
        
        # If not in database or data is stale, fetch from API
        response = await football_api.get_league(league_id)
        if response:
            # Store in database for next time
            if not league:
                league = League(**response['league'])
                db.add(league)
            else:
                for key, value in response['league'].items():
                    setattr(league, key, value)
            
            # Update standings
            standings_data = response.get('standings', [])
            for standing_data in standings_data:
                standing = Standing(**standing_data)
                db.add(standing)
            
            db.commit()
            return {"status": "success", "data": response}
            
        raise HTTPException(status_code=404, detail="League not found")
        
    except Exception as e:
        logger.error(f"Error fetching league: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 