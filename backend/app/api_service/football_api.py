import requests
from fastapi import HTTPException
from dotenv import load_dotenv
import logging
from datetime import datetime
import aiohttp
from ..config import settings


load_dotenv()
logger = logging.getLogger(__name__)

class FootballAPIService:
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": settings.FOOTBALL_API_KEY,
        }
        # Test the API key on initialization
        self.test_api_key()
        
        self.major_leagues = {
            'DFB Pokal': {'id': 529, 'season': 2024},
            'Copa del Rey': {'id': 143, 'season': 2024},
            'Premier League': {'id': 39, 'season': 2024},
            'Bundesliga': {'id': 78, 'season': 2024},
            'LaLiga': {'id': 140, 'season': 2024},
            'Serie A': {'id': 135, 'season': 2024},
            'Ligue 1': {'id': 61, 'season': 2024},
            'Champions League': {'id': 2, 'season': 2024},
            'Europa League': {'id': 3, 'season': 2024}
        }

    def test_api_key(self):
        """Test the API key by making a status request"""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"API key test failed: {response.text}")
                raise ValueError(f"Invalid API key or API error: {response.text}")
                
            logger.info("API key test successful")
            
        except Exception as e:
            logger.error(f"Error testing API key: {str(e)}")
            raise ValueError(f"Error testing API key: {str(e)}")

    def get_current_date(self):
        """Get current date with correct year"""
        current_date = datetime.now()
        return current_date.replace(year=2025).strftime('%Y-%m-%d')

    async def get_team(self, team_id: int = None):
        try:
            url = f"{self.base_url}/teams"
            params = {'id': team_id} if team_id else {}
            
            logger.info(f"Making request to {url} with params {params}")
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params
            )
            
            if response.status_code != 200:
                error_message = f"API request failed: {response.text}"
                logger.error(error_message)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_message
                )
                
            return response.json()
            
        except Exception as e:
            error_message = f"Error fetching team data: {str(e)}"
            logger.error(error_message)
            raise HTTPException(
                status_code=500,
                detail=error_message
            )

    async def get_matches(self, live=False, completed=False):
        try:
            url = f"{self.base_url}/fixtures"
            today = datetime.now().strftime('%Y-%m-%d')
            
            #status types
            LIVE_STATUSES = ['1H', '2H', 'HT', 'ET', 'P', 'LIVE']
            SCHEDULED_STATUSES = ['NS', 'TBD']
            FINISHED_STATUSES = ['FT', 'AET', 'PEN']
            
            params = {
                'date': today,
                'timezone': 'Europe/London'
            }
            
            logger.info(f"Fetching fixtures for date: {today}, completed: {completed}")
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"API request failed: {response.text}"
                )
            
            data = response.json()
            all_matches = data.get('response', [])
            
            # Filter matches based on status
            filtered_matches = []
            for match in all_matches:
                status = match.get('fixture', {}).get('status', {}).get('short')
                league_name = match.get('league', {}).get('name')
                
                # Only process matches from these specific leagues
                logger.info(f"Processing match from league: {league_name}")
                if league_name not in [
                    'Premier League',
                    'LaLiga',
                    'La Liga',  # Alternative spelling
                    'Serie A',
                    'Bundesliga',
                    'Ligue 1',
                    'FA Cup',
                    'DFB Pokal',
                    'Coppa Italia',
                    'Copa del Rey',
                    'Champions League',
                    'Europa League'
                ]:
                    continue
                    
                home_team = match.get('teams', {}).get('home', {})
                away_team = match.get('teams', {}).get('away', {})
                
                # Get elapsed time for live matches
                fixture_status = match.get('fixture', {}).get('status', {})
                elapsed_time = fixture_status.get('elapsed')
                
                if home_team and away_team:
                    home_team['logo'] = home_team.get('logo', '')
                    away_team['logo'] = away_team.get('logo', '')
                
                match['fixture']['elapsed'] = elapsed_time
                
                # For the completed tab, only include finished matches
                if completed and status in FINISHED_STATUSES:
                    filtered_matches.append(match)
                    logger.info(f"Added finished match to completed tab: {league_name} [{status}]")
                    
                # For today tab, only include live and scheduled matches
                elif not completed and (status in LIVE_STATUSES or status in SCHEDULED_STATUSES):
                    filtered_matches.append(match)
                    logger.info(f"Added live/scheduled match to today tab: {league_name} [{status}]")
            
            logger.info(f"Found {len(filtered_matches)} matches for {'completed' if completed else 'today'} tab")
            
            return {
                "response": filtered_matches
            }
                
        except Exception as e:
            logger.error(f"Error in get_matches: {str(e)}")
            return {
                "response": [],
                "errors": str(e)
            }

    async def test_api(self):
        """Test method to verify API connectivity"""
        try:
            url = f"{self.base_url}/fixtures"
            today = self.get_current_date()
            
            params = {
                'date': today,
                'league': '529', 
                'season': '2024'  
            }
            
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('response', [])
                logger.info(f"Found {len(matches)} DFB Pokal matches")
            
            return {
                "status": response.status_code,
                "message": "API test successful" if response.status_code == 200 else "API test failed",
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            logger.error(f"API Test Error: {str(e)}")
            return {
                "status": 500,
                "message": f"API test error: {str(e)}",
                "data": None
            }

    async def get_teams(self, search=None):
        """Fetch teams, optionally filtered by search query"""
        url = f"{self.base_url}/teams"
        params = {}
        if search:
            params["search"] = search
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"Teams API Status Code: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched teams. Count: {len(data.get('response', []))}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching teams: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_teams: {str(e)}")
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
        fixture_url = f"{self.base_url}/fixtures"
        lineups_url = f"{self.base_url}/fixtures/lineups"
        
        try:
            params = {
                "id": match_id,
                "fixture": match_id  
            }
            
            logger.info(f"Requesting match details with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                
                async with session.get(fixture_url, headers=self.headers, params={"id": match_id}) as response:
                    if response.status != 200:
                        logger.error(f"API Error: Status {response.status}")
                        return None

                    match_data = await response.json()
                    
                    fixture_status = match_data.get('response', [{}])[0].get('fixture', {}).get('status', {}).get('short')
                    if fixture_status not in ['TBD', 'CANC', 'PST', 'SUSP']:
                        # Use different params for lineups endpoint
                        lineup_params = {"fixture": match_id}
                        async with session.get(lineups_url, headers=self.headers, params=lineup_params) as lineups_response:
                            logger.info(f"Lineups API response status: {lineups_response.status}")
                            
                            if lineups_response.status == 200:
                                lineups_data = await lineups_response.json()
                                logger.info(f"Lineups data received: {lineups_data}")
                                
                                if lineups_data and 'response' in lineups_data and lineups_data['response']:
                                    if match_data and 'response' in match_data and match_data['response']:
                                        match_data['response'][0]['lineups'] = lineups_data['response']
                                        
                    else:
                        logger.info(f"Skipping lineups request for future match (status: {fixture_status})")
                        if match_data and 'response' in match_data and match_data['response']:
                            match_data['response'][0]['lineups'] = []
                
                return match_data

        except Exception as e:
            logger.error(f"Exception in get_match_details: {str(e)}")
            raise

    async def get_leagues(self):
        """Fetch all available leagues"""
        url = f"{self.base_url}/leagues"
        params = {
            "current": "true" 
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"Leagues API Status Code: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Successfully fetched leagues. Count: {len(data.get('response', []))}")
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching leagues: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_leagues: {str(e)}")
            raise 

    async def get_standings(self, league_id: int, season: int):
        """Fetch standings for a specific league and season"""
        url = f"{self.base_url}/standings"
        params = {
            "league": league_id,
            "season": season
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching standings: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_standings: {str(e)}")
            raise 

    async def get_team_players(self, team_id: int, season: int):
        """Fetch squad for a specific team"""
        url = f"{self.base_url}/players/squads"
        params = {
            "team": team_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching team players: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_team_players: {str(e)}")
            raise

    async def get_team_matches(self, team_id: int, next: int = None, last: int = None):
        """Fetch matches for a specific team"""
        url = f"{self.base_url}/fixtures"
        params = {
            "team": team_id
        }
        
        if next:
            params["next"] = next
        if last:
            params["last"] = last
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error fetching team matches: {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Exception in get_team_matches: {str(e)}")
            raise

    async def get_team_statistics(self, team_id: int, league_id: int = None, season: int = None):
        """Fetch team statistics"""
        url = f"{self.base_url}/teams/statistics"
        
        try:
            
            if not season:
                current_date = datetime.now()
                season = current_date.year
                if current_date.month < 8:  # If before August, use previous year
                    season -= 1

            if not league_id:
                logger.error("League ID is required for team statistics")
                return None

            params = {
                "team": team_id,
                "league": league_id,
                "season": season
            }
            
            logger.info(f"Requesting team statistics with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"Team statistics API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API Error: Status {response.status}, Response: {error_text}")
                        return None

                    data = await response.json()
                    logger.info(f"API Response data: {data}")
                    
                    if not data or 'response' not in data:
                        logger.error("Invalid response format from API")
                        return None

                    return data

        except Exception as e:
            logger.error(f"Exception in get_team_statistics: {str(e)}")
            raise 

    
    async def get_player_statistics(self, season: int, player_id: int, team: int = None):
        """Get player statistics"""
        url = f"{self.base_url}/players"
        params = {
            "id": player_id,
            "season": season
        }
        
        if team:
            params["team"] = team
        
        logger.info(f"Fetching player statistics with params: {params}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    logger.info(f"API Response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API Error: Status {response.status}, Response: {error_text}")
                        return None

                    data = await response.json()
                    logger.info(f"API Response data: {data}")
                    
                
                    if data.get('errors'):
                        logger.error(f"API returned errors: {data['errors']}")
                        return None

                    return data
                    
        except Exception as e:
            logger.error(f"Error getting player statistics: {str(e)}")
            return None

    async def get_team_info(self, team_id: int):
        """Get team information including league ID"""
        url = f"{self.base_url}/teams"
        params = {"id": team_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    return data if data.get('response') else None
                
        except Exception as e:
            logger.error(f"Error getting team info: {str(e)}")
            return None

    async def get_team_squad(self, team_id: int, season: int):
        """Fetch team squad"""
        url = f"{self.base_url}/players/squads"
        
        try:
            params = {
                "team": team_id
            }
            
            headers = {
                "x-rapidapi-host": "v3.football.api-sports.io",
                "x-rapidapi-key": self.headers["x-apisports-key"]
            }
            
            logger.info(f"Requesting team squad with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    logger.info(f"Team squad API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API Error: Status {response.status}, Response: {error_text}")
                        return None

                    data = await response.json()
                    
                    # Check for API errors
                    if data.get('errors'):
                        logger.error(f"API returned errors: {data['errors']}")
                        return None

                    return data

        except Exception as e:
            logger.error(f"Exception in get_team_squad: {str(e)}")
            raise 