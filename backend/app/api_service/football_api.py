import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from datetime import datetime
from ..config import settings
from json.decoder import JSONDecodeError
from sqlalchemy.exc import SQLAlchemyError

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
        """Test API key validity during initialization."""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers,
                timeout=30
            )
            if response.status_code != 200:
                raise ValueError("Invalid API key")
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="API connection error")

    def get_current_date(self):
        """Get current date with correct year"""
        try:
            current_date = datetime.now()
            return current_date.replace(year=2025).strftime('%Y-%m-%d')
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    def get_team(self, team_id: int = None):
        """Get team information by ID."""
        try:
            url = f"{self.base_url}/teams"
            params = {'id': team_id} if team_id else {}

            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="API request failed"
                )
            
            return response.json()
            
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch team data")

    def get_matches(self, live=False, completed=False):
        """Get matches for today, filtered by status."""
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
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="API request failed"
                )
            
            data = response.json()
            all_matches = data.get('response', [])
            
            filtered_matches = []
            for match in all_matches:
                status = match.get('fixture', {}).get('status', {}).get('short')
                league_name = match.get('league', {}).get('name')
                
                if league_name not in [
                    'Premier League',
                    'LaLiga',
                    'La Liga',
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
                
                fixture_status = match.get('fixture', {}).get('status', {})
                elapsed_time = fixture_status.get('elapsed')
                
                if home_team and away_team:
                    home_team['logo'] = home_team.get('logo', '')
                    away_team['logo'] = away_team.get('logo', '')
                
                match['fixture']['elapsed'] = elapsed_time
                
                if completed and status in FINISHED_STATUSES:
                    filtered_matches.append(match)
                elif not completed and (status in LIVE_STATUSES or status in SCHEDULED_STATUSES):
                    filtered_matches.append(match)
        
            return {
                "response": filtered_matches
            }
                
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch matches")

    def test_api(self):
        """Test method to verify API connectivity."""
        try:
            url = f"{self.base_url}/fixtures"
            today = self.get_current_date()
            
            params = {
                'date': today,
                'league': '529', 
                'season': '2024'  
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
        
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": response.status_code,
                    "message": "API test successful",
                    "data": data
                }
        
            return {
                "status": response.status_code,
                "message": "API test failed",
                "data": None
            }
                
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Request failed")

    def get_teams(self, league_id: int, season: int = 2024):
        """Get teams for a specific league and season"""
        try:
            url = f"{self.base_url}/teams"
            params = {
                "league": league_id,
                "season": season
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="API request failed")
            return response.json()
            
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch teams")

    def get_players(self, search=None):
        """Fetch players, optionally filtered by search query."""
        try:
            url = f"{self.base_url}/players"
            params = {
                "search": search
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
                    
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch players")

    def get_match_details(self, match_id: int):
        """Get detailed match information including lineups and substitutions."""
        try:
            fixture_url = f"{self.base_url}/fixtures"
            lineups_url = f"{self.base_url}/fixtures/lineups"
            events_url = f"{self.base_url}/fixtures/events"
            
            response = requests.get(
                fixture_url, 
                headers=self.headers, 
                params={"id": match_id},
                timeout=30
            )
            
            if response.status_code != 200:
                return None

            match_data = response.json()
            if not match_data.get('response'):
                return None
            
            fixture_status = match_data.get('response', [{}])[0].get('fixture', {}).get('status', {}).get('short')
            if fixture_status in ['TBD', 'CANC', 'PST', 'SUSP']:
                match_data['response'][0]['lineups'] = []
                match_data['response'][0]['events'] = []
                return match_data
            
            lineups_response = requests.get(
                lineups_url, 
                headers=self.headers, 
                params={"fixture": match_id},
                timeout=30
            )
            if lineups_response.status_code == 200:
                lineups_data = lineups_response.json()
                if lineups_data and 'response' in lineups_data:
                    match_data['response'][0]['lineups'] = lineups_data['response']
        
            events_response = requests.get(
                events_url,
                headers=self.headers,
                params={"fixture": match_id},
                timeout=30
            )
            if events_response.status_code == 200:
                events_data = events_response.json()
                if events_data and 'response' in events_data:
                    substitutions = [
                        event for event in events_data['response']
                        if event.get('type') == 'subst'
                    ]
                    match_data['response'][0]['substitutions'] = substitutions
        
            return match_data

        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch match details")

    def get_leagues(self):
        """Get all current leagues."""
        try:
            url = f"{self.base_url}/leagues"
            params = {
                "current": "true" 
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="API request failed")
            return response.json()
            
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_standings(self, league_id: int, season: int):
        """Get league standings."""
        try:
            url = f"{self.base_url}/standings"
            params = {
                "league": league_id,
                "season": season
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_team_players(self, team_id: int, season: int):
        """Get squad list for a team."""
        try:
            url = f"{self.base_url}/players/squads"
            params = {
                "team": team_id
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_team_matches(self, team_id: int, next: int = None, last: int = None):
        """Get matches for a specific team."""
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                "team": team_id
            }
            
            if next:
                params["next"] = next
            if last:
                params["last"] = last
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_team_statistics(self, team_id: int, league_id: int = None, season: int = None):
        """Get team statistics for a specific league and season."""
        try:
            url = f"{self.base_url}/teams/statistics"
            
            if not league_id:
                return None
            
            if not season:
                current_date = datetime.now()
                season = current_date.year
                if current_date.month < 8:  # If before August, use previous year
                    season -= 1

            params = {
                "team": team_id,
                "league": league_id,
                "season": season
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return None

            data = response.json()
            
            if data.get("errors"):
                return None

            return data

        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")
        
    def get_player_statistics(self, season: int, player_id: int, team: int = None):
        """Get player statistics for a season."""
        try:
            url = f"{self.base_url}/players"
            params = {
                "id": player_id,
                "season": season
            }
            
            if team:
                params["team"] = team
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return None

            data = response.json()
            
            if data.get('errors'):
                return None

            return data
                    
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_team_info(self, team_id: int):
        """Get detailed team information."""
        try:
            url = f"{self.base_url}/teams"
            params = {"id": team_id}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get("errors"):
                return None
            
            return data
                
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")

    def get_team_squad(self, team_id: int, season: int):
        """Fetch team squad"""
        try:
            url = f"{self.base_url}/players/squads"
            params = {
                "team": team_id
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return None

            data = response.json()
            if data.get('errors'):
                return None

            return data

        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")
        
    def get_countries(self):
        """Get all countries from API-FOOTBALL"""
        try:
            url = f"{self.base_url}/countries"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch countries"
                )
                
            data = response.json()
            return data
                        
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON response from API")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parameter value")
        except SQLAlchemyError:
            raise HTTPException(status_code=500, detail="Database error")
        except requests.RequestException:
            raise HTTPException(status_code=500, detail="Failed to fetch leagues")