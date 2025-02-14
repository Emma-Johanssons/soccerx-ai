from fastapi import APIRouter, HTTPException
from ..api_service.football_api import FootballAPIService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/{league_id}/{season}")
async def get_standings(league_id: int, season: int):
    try:
        logger.info(f"Fetching standings for league {league_id}, season {season}")
        response = await football_api.get_standings(league_id, season)
        
        if response and 'response' in response:
            standings = response['response'][0]['league']['standings'][0]
            return {
                "status": "success",
                "data": standings,
                "message": "Standings retrieved successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="No standings found")
            
    except Exception as e:
        logger.error(f"Error fetching standings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching standings: {str(e)}"
        ) 