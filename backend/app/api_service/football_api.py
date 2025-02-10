import requests
from fastapi import HTTPException
from datetime import datetime, timedelta
import aiohttp
from ..config import settings

class FootballAPIService:
    def __init__(self):
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": settings.FOOTBALL_API_KEY,
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

    async def get_matches(self, live=False, completed=False):
        try:
            url = f"{self.base_url}/fixtures"
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Define status types
            LIVE_STATUSES = ['1H', '2H', 'HT', 'ET', 'P', 'LIVE']
            SCHEDULED_STATUSES = ['NS', 'TBD']
            FINISHED_STATUSES = ['FT', 'AET', 'PEN']
            
            params = {
                'date': today,
                'timezone': 'Europe/London'
            }
            
            
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params
            )
            
            if response.status_code != 200:
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
                if league_name not in [
                    'Premier League',
                    'LaLiga',
                    'La Liga',  # Add alternative spelling
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
                    
                # Add team logos and match time
                home_team = match.get('teams', {}).get('home', {})
                away_team = match.get('teams', {}).get('away', {})
                
                # Get elapsed time for live matches
                fixture_status = match.get('fixture', {}).get('status', {})
                elapsed_time = fixture_status.get('elapsed')
                
                # Ensure we have the logo URLs and elapsed time
                if home_team and away_team:
                    home_team['logo'] = home_team.get('logo', '')
                    away_team['logo'] = away_team.get('logo', '')
                
                # Add elapsed time to the match data
                match['fixture']['elapsed'] = elapsed_time
                
                # For completed tab, only include finished matches
                if completed and status in FINISHED_STATUSES:
                    filtered_matches.append(match)
                    
                # For today tab, only include live and scheduled matches
                elif not completed and (status in LIVE_STATUSES or status in SCHEDULED_STATUSES):
                    filtered_matches.append(match)
            
            
            return {
                "response": filtered_matches
            }
                
        except Exception as e:
            return {
                "response": [],
                "errors": str(e)
            }