from fastapi import HTTPException
from datetime import datetime
import aiohttp
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class FootballAPIService:
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": settings.FOOTBALL_API_KEY
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
            raise

    async def get_players(self, search=None):
        """Fetch players, optionally filtered by search query"""
        url = f"{self.base_url}/players"
        params = {
            "search": search
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"Players API Status Code: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched players. Count: {len(data.get('response', []))}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching players: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_players: {str(e)}")
            raise

    async def get_match_details(self, match_id: int):
        """Fetch detailed information about a specific match"""
        try:
            logger.info(f"Requesting match details for match {match_id}")
            
            async with aiohttp.ClientSession() as session:
                # Get match details first
                fixture_response = await session.get(
                    f"{self.base_url}/fixtures",
                    headers=self.headers,
                    params={"id": match_id}
                )
                
                if fixture_response.status != 200:
                    logger.error(f"Fixture API Error: Status {fixture_response.status}")
                    return None

                match_data = await fixture_response.json()
                match_info = match_data.get('response', [{}])[0]
                league_id = match_info.get('league', {}).get('id')
                league_name = match_info.get('league', {}).get('name')
                
                # Get lineups
                lineups_response = await session.get(
                    f"{self.base_url}/fixtures/lineups",
                    headers=self.headers,
                    params={"fixture": match_id}
                )
                
                if lineups_response.status == 200:
                    lineups_data = await lineups_response.json()
                    
                    if lineups_data.get('results', 0) > 0 and lineups_data.get('response'):
                        logger.info(f"Found lineup data for {len(lineups_data['response'])} teams")
                        match_data['response'][0]['lineups'] = lineups_data['response']
                    else:
                        logger.info(f"No lineup data available yet for match {match_id} in {league_name}")
                        logger.info("This could be because:")
                        logger.info("1. Lineups haven't been announced yet (usually 20-40 min before kickoff)")
                        logger.info("2. The league doesn't provide lineup data")
                        logger.info("3. The match hasn't started yet")
                        logger.info(f"League ID: {league_id}, League Name: {league_name}")
                        match_data['response'][0]['lineups'] = []
                else:
                    error_text = await lineups_response.text()
                    logger.error(f"Failed to fetch lineups: {error_text}")
                    match_data['response'][0]['lineups'] = []

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
                "status": "NS-TBD"  #NS = NOT STARTED
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