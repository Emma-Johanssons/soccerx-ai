from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..sql_models.models import League, Team, LeagueStandings
from ..api_service.football_api import FootballAPIService
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()
football_api = FootballAPIService()

@router.get("/")
async def get_leagues():
    try:
        logger.info("Starting leagues fetch request")
        response = football_api.get_leagues()
        
        logger.info(f"Raw API response received: {response}")
        
        if response and 'response' in response:
            leagues = response['response']
            logger.info(f"Found {len(leagues)} leagues")
            
            # Format the leagues data
            formatted_leagues = []
            
            for league in leagues:
                if league.get('league'):
                    league_name = league['league']['name']
                    country_name = league['country']['name']
                    
                    # Special handling for Premier League
                    if league_name == "Premier League":
                        # Append country name to Premier League
                        display_name = f"Premier League - {country_name}"
                    else:
                        display_name = league_name
                        
                    formatted_leagues.append({
                        'league': {
                            'id': league['league']['id'],
                            'name': display_name,  # Use the modified name
                            'type': league['league']['type'],
                            'logo': league['league'].get('logo'),
                            'country': country_name
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
async def get_league(league_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching league with ID: {league_id} from database")
        
        # First try to get from database
        league = db.query(League).filter(League.id == league_id).first()
        
        # Try to get standings from database first
        standings = db.query(LeagueStandings).filter(
            LeagueStandings.league_id == league_id
        ).first()
        
        if league:
            # Get teams for this league from database
            teams = db.query(Team).filter(Team.league == league_id).all()
            
            # If standings exist and are fresh (less than 24 hours old)
            if standings and (datetime.now() - standings.last_updated) < timedelta(hours=24):
                standings_data = standings.to_dict()  # Assuming you have a to_dict method
            else:
                # Get standings from API and store in database
                standings_response = football_api.get_standings(league_id, 2024)
                if standings_response and 'response' in standings_response:
                    standings_data = standings_response['response'][0]['league']['standings']
                    
                    # Store or update standings in database
                    if not standings:
                        standings = LeagueStandings(league_id=league_id)
                    
                    standings.data = standings_data  # Assuming you store as JSON
                    standings.last_updated = datetime.now()
                    db.add(standings)
                    db.commit()
                else:
                    standings_data = []
            
            return {
                "status": "success",
                "data": {
                    "league": {
                        "id": league.id,
                        "name": league.name,
                        "logo": league.logo,
                        "type": "League"
                    },
                    "country": {
                        "name": league.country
                    },
                    "seasons": [
                        {
                            "year": 2024,
                            "current": True,
                            "standings": standings_data
                        }
                    ],
                    "teams": [
                        {
                            "id": team.id,
                            "name": team.name,
                            "logo": team.logo_url,
                            "venue_name": team.venue_name,
                            "venue_capacity": team.venue_capacity
                        } for team in teams
                    ]
                },
                "message": "League retrieved successfully"
            }
        
        # If not in database, fallback to API
        logger.info(f"League not found in database, fetching from API")
        response = football_api.get_leagues()
        
        if response and 'response' in response:
            leagues = response['response']
            league_data = next(
                (league for league in leagues 
                 if league['league']['id'] == league_id), 
                None
            )
            
            if league_data:
                standings_response =  football_api.get_standings(league_id, 2024)
                
                return {
                    "status": "success",
                    "data": {
                        "league": league_data['league'],
                        "country": league_data['country'],
                        "seasons": [
                            {
                                "year": 2024,
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