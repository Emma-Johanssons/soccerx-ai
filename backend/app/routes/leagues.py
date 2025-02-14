from fastapi import APIRouter, HTTPException
from ..api_service.football_api import FootballAPIService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/")
async def get_leagues():
    try:
        logger.info("Starting leagues fetch request")
        response = await football_api.get_leagues()
        
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
async def get_league(league_id: int):
    try:
        logger.info(f"Fetching league with ID: {league_id}")
        # Get current season
        current_season = 2024  # You can make this dynamic if needed
        
        # Get league information
        response = await football_api.get_leagues()
        
        if response and 'response' in response:
            leagues = response['response']
            league_data = next(
                (league for league in leagues 
                 if league['league']['id'] == league_id), 
                None
            )
            
            if league_data:
                # Get standings for the league
                standings_response = await football_api.get_standings(league_id, current_season)
                
                # Combine league data with standings
                return {
                    "status": "success",
                    "data": {
                        "league": league_data['league'],
                        "country": league_data['country'],
                        "seasons": [
                            {
                                "year": current_season,
                                "current": True,
                                "standings": standings_response['response'][0]['league']['standings'] if standings_response and 'response' in standings_response else []
                            }
                        ]
                    },
                    "message": "League retrieved successfully"
                }
                
        raise HTTPException(status_code=404, detail=f"League with ID {league_id} not found")
        
    except Exception as e:
        logger.error(f"Error fetching league: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching league: {str(e)}"
        ) 