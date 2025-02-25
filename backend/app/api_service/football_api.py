import requests
from fastapi import HTTPException
from dotenv import load_dotenv
from datetime import datetime
from ..config import settings
from json.decoder import JSONDecodeError
from sqlalchemy.exc import SQLAlchemyError
import logging

load_dotenv()

logger = logging.getLogger(__name__)

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
        self.base_url = settings.API_BASE_URL
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

    def get_matches(self, date: str):
        """Fetch matches for a specific date"""
        try:
            url = f"{self.base_url}/fixtures"
            params = {'date': date}
            logger.info(f"Fetching matches with params: {params}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="API request failed"
                )
            
            data = response.json()
            logger.info(f"Got response from API: {data}")
            return data
            
        except requests.ConnectionError:
            raise HTTPException(status_code=503, detail="API service unavailable")
        except requests.Timeout:
            raise HTTPException(status_code=504, detail="Request timeout")
        except Exception as e:
            logger.error(f"Error in get_matches: {str(e)}")
            raise

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
                "search": search,
                "include": "birth,nationality"
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
            
            # Only skip lineups for matches that haven't started or were cancelled
            if fixture_status in ['TBD', 'CANC', 'PST', 'SUSP', 'NS']:
                match_data['response'][0]['lineups'] = []
                match_data['response'][0]['events'] = []
                return match_data
            
            # Fetch lineups for all other statuses (including FT - full time)
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
                else:
                    match_data['response'][0]['lineups'] = []  # Empty if no lineup data
            
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

    def get_team_players(self, team_id: int):
        """Get players for a specific team."""
        try:
            url = f"{self.base_url}/players/squads"
            params = {
                "team": team_id
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code != 200:
                return None

            data = response.json()
            
            # Log the response to see the data structure
            logger.info(f"API Response for team {team_id}: {data}")
            
            if data.get("errors"):
                return None

            return data
                
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to fetch team players")

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
            
            if not season:
                current_date = datetime.now()
                season = current_date.year
                if current_date.month < 8:  # If before August, use previous year
                    season -= 1

            params = {
                "team": team_id,
                "season": season
            }
            
            if league_id:
                params["league"] = league_id
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                return None

            data = response.json()
            
            if data.get("errors"):
                return None

            return data

        except Exception as e:
            logger.error(f"Error fetching team statistics: {str(e)}")
            return None

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