import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from datetime import datetime
import aiohttp
import asyncio
from ..config import settings


load_dotenv()

class FootballAPIService:
    """
    Service class for handling football API requests.
    
    This class provides methods to interact with the football API for retrieving
    data about matches, teams, players, leagues, and statistics. It handles API
    authentication, request formatting, and error handling.
    
    Attributes:
        base_url (str): Base URL for the football API
        headers (dict): API authentication headers
        major_leagues (dict): Configuration for supported major leagues
    """
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": settings.FOOTBALL_API_KEY,
        }
        if not settings.FOOTBALL_API_KEY:
            raise ValueError("Missing API key")
        self._test_api_key_sync()
        
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

    def _test_api_key_sync(self):
        """
        Synchronously test API key validity during initialization.
        
        This method is called during class initialization to verify
        that the API key is valid and the service is accessible.
        
        Raises:
            ValueError: If API key is invalid or connection fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers,
                timeout=30
            )
            if response.status_code != 200:
                raise ValueError("Invalid API key")
        except requests.RequestException as e:
            raise ValueError(f"API connection error: {str(e)}")

    def get_current_date(self):
        """
        Get current date with correct year
        """
        current_date = datetime.now()
        return current_date.replace(year=2025).strftime('%Y-%m-%d')

    async def get_team(self, team_id: int = None):
        """
        Get team information by ID.
        
        Args:
            team_id (int, optional): Team ID to fetch. If None, returns all teams.
            
        Returns:
            dict: Team data from API
            
        Raises:
            HTTPException: If API request fails or times out
        """
        try:
            url = f"{self.base_url}/teams"
            params = {'id': team_id} if team_id else {}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="API request failed"
                        )
                
                    return await response.json()
                
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")
        
            

    async def get_matches(self, live=False, completed=False):
        """
        Get matches for today, filtered by status.
        
        Args:
            live (bool): If True, include only live matches
            completed (bool): If True, include only completed matches
            
        Returns:
            dict: Filtered matches data with "response" key
            
        Raises:
            HTTPException: If API request fails or times out
        """
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
                        
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    
                    if response.status != 200:
                        raise HTTPException(
                            status_code=response.status,
                            detail="API request failed"
                        )
                    
                    data = await response.json()
                    all_matches = data.get('response', [])
                    
                    # Filter matches based on status
                    filtered_matches = []
                    for match in all_matches:
                        status = match.get('fixture', {}).get('status', {}).get('short')
                        league_name = match.get('league', {}).get('name')
                        
                        # Only process matches from these specific leagues
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
                            
                        # For today tab, only include live and scheduled matches
                        elif not completed and (status in LIVE_STATUSES or status in SCHEDULED_STATUSES):
                            filtered_matches.append(match)
            
            
            return {
                "response": filtered_matches
            }
                
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")
        

    async def test_api(self):
        """
        Test method to verify API connectivity.
        
        Makes a test request to the fixtures endpoint to verify API access
        and authentication.
        
        Returns:
            dict: Response containing:
                - status (int): HTTP status code
                - message (str): Success/failure message
                - data (dict): API response data if successful
            
        Raises:
            HTTPException: If API request fails or times out
        """
        try:
            url = f"{self.base_url}/fixtures"
            today = self.get_current_date()
            
            params = {
                'date': today,
                'league': '529', 
                'season': '2024'  
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
            
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": response.status,
                            "message": "API test successfull",
                            "data": data
                        }
            
                    return {
                        "status": response.status,
                        "message":"API test failed",
                        "data": None
                    }
                
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")
      

    async def get_teams(self, search=None):
        """
        Search for teams by name.
        
        Args:
            search (str, optional): Team name to search for
            
        Returns:
            dict: Team search results or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """        
        url = f"{self.base_url}/teams"
        params = {}
        if search:
            params["search"] = search
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return None
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code= 504, detail="Timeout error")
        

    async def get_players(self, search=None):
        """
        Fetch players, optionally filtered by search query.
        
        Args:
            search (str, optional): Search term to filter players by name
            
        Returns:
            dict: Player search results or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
        url = f"{self.base_url}/players"
        params = {
            "search": search
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        return None
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")
       

    async def get_match_details(self, match_id: int):
        """
        Get detailed match information including lineups and substitutions.
        
        Args:
            match_id (int): The unique identifier of the match
            
        Returns:
            dict: Match details including:
                - Basic match information
                - Lineups for both teams
                - Starting XI
                - Substitutes
                - Coach information
                - Formation
                - Events (including substitutions)
            Returns None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
        fixture_url = f"{self.base_url}/fixtures"
        lineups_url = f"{self.base_url}/fixtures/lineups"
        events_url = f"{self.base_url}/fixtures/events"
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get match details
                async with session.get(
                    fixture_url, 
                    headers=self.headers, 
                    params={"id": match_id}
                ) as response:
                    if response.status != 200:
                        return None

                    match_data = await response.json()
                    if not match_data.get('response'):
                        return None
                    
                    # Check if match is scheduled/cancelled
                    fixture_status = match_data.get('response', [{}])[0].get('fixture', {}).get('status', {}).get('short')
                    if fixture_status in ['TBD', 'CANC', 'PST', 'SUSP']:
                        match_data['response'][0]['lineups'] = []
                        match_data['response'][0]['events'] = []
                        return match_data
                    
                    # Get lineups
                    async with session.get(
                        lineups_url, 
                        headers=self.headers, 
                        params={"fixture": match_id}
                    ) as lineups_response:
                        if lineups_response.status == 200:
                            lineups_data = await lineups_response.json()
                            if lineups_data and 'response' in lineups_data:
                                match_data['response'][0]['lineups'] = lineups_data['response']
                
                    # Get events (including substitutions)
                    async with session.get(
                        events_url,
                        headers=self.headers,
                        params={"fixture": match_id}
                    ) as events_response:
                        if events_response.status == 200:
                            events_data = await events_response.json()
                            if events_data and 'response' in events_data:
                                # Filter for substitution events
                                substitutions = [
                                    event for event in events_data['response']
                                    if event.get('type') == 'subst'
                                ]
                                match_data['response'][0]['substitutions'] = substitutions
                
                    return match_data

        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")
        

    async def get_leagues(self):
        """
        Get all current leagues.
        
        Returns:
            dict: League data from API
            
        Raises:
            HTTPException: If API request fails or times out
        """
        url = f"{self.base_url}/leagues"
        params = {
            "current": "true" 
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    return await response.json()
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")
        
        
    async def get_standings(self, league_id: int, season: int):
        """
        Get league standings.
        
        Args:
            league_id (int): League ID to fetch standings for
            season (int): Season year
            
        Returns:
            dict: League standings data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
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
                        return None
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")
        
        
    async def get_team_players(self, team_id: int, season: int):
        """
        Get squad list for a team.
        
        Args:
            team_id (int): Team ID to fetch squad for
            season (int): Season year
            
        Returns:
            dict: Team squad data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
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
                        return None
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Timeout error")

    async def get_team_matches(self, team_id: int, next: int = None, last: int = None):
        """
        Get matches for a specific team.
        
        Args:
            team_id (int): Team ID to fetch matches for
            next (int, optional): Number of upcoming matches to fetch
            last (int, optional): Number of past matches to fetch
            
        Returns:
            dict: Team matches data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
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
                        return None
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")

    async def get_team_statistics(self, team_id: int, league_id: int = None, season: int = None):
        """
        Get team statistics for a specific league and season.
        
        Args:
            team_id (int): Team ID to fetch statistics for
            league_id (int, optional): League ID for statistics
            season (int, optional): Season year, defaults to current season
            
        Returns:
            dict: Team statistics data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
        url = f"{self.base_url}/teams/statistics"
        
        try:
            if not league_id:
                return None
            
            if not season:
                current_date = datetime.now()
                season = current_date.year
                if current_date.month < 8:  # If before August, use previous year
                    season -= 1

            if not league_id:
                return None

            params = {
                "team": team_id,
                "league": league_id,
                "season": season
            }
            
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    
                    if response.status != 200:
                        return None

                    data = await response.json()
                    
                    if data.get("errors"):
                        return None

                    return data

        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")

    
    async def get_player_statistics(self, season: int, player_id: int, team: int = None):
        """
        Get player statistics for a season.
        
        Args:
            season (int): Season year
            player_id (int): Player ID to fetch statistics for
            team (int, optional): Team ID to filter statistics
            
        Returns:
            dict: Player statistics data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
        url = f"{self.base_url}/players"
        params = {
            "id": player_id,
            "season": season
        }
        
        if team:
            params["team"] = team
        
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:                    
                    if response.status != 200:
                        return None

                    data = await response.json()
                    
                    if data.get('errors'):
                        return None

                    return data
                    
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")
       

    async def get_team_info(self, team_id: int):
        """
        Get detailed team information.
        
        Args:
            team_id (int): Team ID to fetch information for
            
        Returns:
            dict: Team information data or None if request fails
            
        Raises:
            HTTPException: If API request fails or times out
        """
        url = f"{self.base_url}/teams"
        params = {"id": team_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    if data.get("errors"):
                        return None
                    
                    return data
                
        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")
        

    async def get_team_squad(self, team_id: int, season: int):
        """Fetch team squad"""
        url = f"{self.base_url}/players/squads"
        
        try:
            params = {
                "team": team_id
            }
            
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:                    
                    if response.status != 200:
                        return None

                    data = await response.json()
                    if data.get('errors'):
                        return None

                    return data

        except aiohttp.ClientError:
            raise HTTPException(status_code=500, detail="Client error")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504,detail="Timeout error")
       