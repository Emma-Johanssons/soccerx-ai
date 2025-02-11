import requests
from fastapi import HTTPException
from datetime import datetime, timedelta
import aiohttp
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class FootballAPIService:
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-rapidapi-host": "v3.football.api-sports.io",
            "x-rapidapi-key": settings.FOOTBALL_API_KEY
        }

    async def get_teams(self, search=None):
        """Hämta lag, kan filtrera med sökord"""
        url = f"{self.base_url}/teams"
        params = {"search": search} if search else {}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                raise HTTPException(status_code=response.status, detail="Kunde inte hämta lag")

    async def get_matches(self, completed: bool = False, live: bool = False):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/fixtures"
            params = {
                "date": today,
            }
            
            if live:
                params["status"] = "LIVE-1H-2H-HT-ET-P-BT"
            else:
                params["status"] = "FT-PEN-AET-FT" if completed else "NS-1H-2H-HT-ET-P-BT-LIVE"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        raise HTTPException(status_code=500, detail="Failed to fetch matches from external API")
                    
                    data = await response.json()
            
            logger.info(f"Received {len(data.get('response', []))} matches from the API")
            leagues = set(match.get('league', {}).get('name') for match in data.get('response', []))
            logger.info(f"Leagues received: {leagues}")

            return data

        except Exception as e:
            logger.error(f"Error fetching matches: {str(e)}")
            raise e

    async def get_match_details(self, match_id: int):
        """Fetch detailed information about a specific match"""
        fixture_url = f"{self.base_url}/fixtures"
        lineups_url = f"{self.base_url}/fixtures/lineups"
        
        try:
            logger.info(f"Requesting match details for match {match_id}")
            
            async with aiohttp.ClientSession() as session:
                # First get match details
                async with session.get(
                    fixture_url, 
                    headers=self.headers, 
                    params={"id": match_id}
                ) as response:
                    if response.status != 200:
                        logger.error(f"Fixture API Error: Status {response.status}")
                        return None

                    match_data = await response.json()
                    logger.info(f"Match data received")

                # Then get lineups in a separate request
                async with session.get(
                    lineups_url, 
                    headers=self.headers, 
                    params={"fixture": match_id}
                ) as lineups_response:
                    logger.info(f"Lineups API response status: {lineups_response.status}")
                    
                    if lineups_response.status == 200:
                        lineups_data = await lineups_response.json()
                        logger.info(f"Lineups response: {lineups_data}")
                        
                        if lineups_data and 'response' in lineups_data:
                            if match_data and 'response' in match_data and match_data['response']:
                                match_data['response'][0]['lineups'] = lineups_data['response']
                                logger.info(f"Successfully added lineups to match data")
                    else:
                        logger.error(f"Failed to fetch lineups: {await lineups_response.text()}")
                
                return match_data

        except Exception as e:
            logger.error(f"Exception in get_match_details: {str(e)}")
            raise

    async def get_upcoming_matches(self, team_id: int, limit: int = 5):
        """Fetch upcoming matches for a specific team"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                "team": team_id,
                "next": limit,
                "status": "NS-TBD"  # Not Started matches only
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API request failed with status {response.status}: {error_text}")
                        raise HTTPException(status_code=500, detail="Failed to fetch upcoming matches")
                    
                    data = await response.json()
                    return data

        except Exception as e:
            logger.error(f"Error fetching upcoming matches: {str(e)}")
            raise e