from fastapi import APIRouter, HTTPException
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime

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
async def search(q: str):
    try:
        logger.info(f"Received search query: {q}")
        results = []

        # Search leagues
        leagues_response = await football_api.get_leagues()
        if leagues_response and 'response' in leagues_response:
            leagues = [
                {
                    'id': league['league']['id'],
                    'name': league['league']['name'],
                    'type': 'league',
                    'logo': league['league'].get('logo'),
                    'country': league['country']['name']
                }
                for league in leagues_response['response']
                if q.lower() in league['league']['name'].lower()
            ]
            results.extend(leagues)

        # Search teams
        teams_response = await football_api.get_teams(search=q)
        if teams_response and 'response' in teams_response:
            teams = [
                {
                    'id': team['team']['id'],
                    'name': team['team']['name'],
                    'type': 'team',
                    'logo': team['team'].get('logo'),
                    'country': team['team'].get('country')
                }
                for team in teams_response['response']
            ]
            results.extend(teams)

        
        return {
            "status": "success",
            "results": results[:10],  # Limit to top 10 results
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 