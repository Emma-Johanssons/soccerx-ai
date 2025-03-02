from sqlalchemy.orm import Session
from .database import engine, SessionLocal, create_tables
from .api_service.football_api import FootballAPIService
from .sql_models.models import Country, League, Position, Team, Player
from .utils.position_mapper import get_position_id
import asyncio
from datetime import datetime
import logging

football_api = FootballAPIService()
logger = logging.getLogger(__name__)

async def init_countries(db: Session):
    try:
        # Fetch countries from API-FOOTBALL
        response = await football_api.get_countries()
        if response and 'response' in response:
            for country_data in response['response']:
                country = Country(
                    id=country_data.get('id'),
                    country_name=country_data.get('name')
                )
                existing_country = db.query(Country).filter(Country.id == country.id).first()
                if not existing_country:
                    db.add(country)
            db.commit()
            print("Countries initialized successfully")
    except Exception as e:
        print(f"Error initializing countries: {str(e)}")
        db.rollback()

async def init_leagues(db: Session):
    try:
        # Fetch leagues from API-FOOTBALL
        response = await football_api.get_leagues()
        if response and 'response' in response:
            for league_data in response['response']:
                league = League(
                    id=league_data['league']['id'],
                    name=league_data['league']['name']
                )
                existing_league = db.query(League).filter(League.id == league.id).first()
                if not existing_league:
                    db.add(league)
            db.commit()
            print("Leagues initialized successfully")
    except Exception as e:
        print(f"Error initializing leagues: {str(e)}")
        db.rollback()

def init_positions(db: Session):
    """Initialize static position data"""
    positions = [
        {"id": 1, "positions": "Goalkeeper"},
        {"id": 2, "positions": "Defender"},
        {"id": 3, "positions": "Midfielder"},
        {"id": 4, "positions": "Attacker"}
    ]
    
    try:
        for pos_data in positions:
            position = Position(**pos_data)
            existing_position = db.query(Position).filter(Position.id == position.id).first()
            if not existing_position:
                db.add(position)
                print(f"Adding position: {position.positions}")
        db.commit()
        print("Positions initialized successfully")
    except Exception as e:
        print(f"Error initializing positions: {str(e)}")
        db.rollback()
        raise  # Re-raise to ensure initialization fails if positions can't be created

async def init_teams(db: Session):
    """Initialize teams for major leagues"""
    try:
        leagues = db.query(League).all()
        for league in leagues:
            response = await football_api.get_teams_by_league(league.id)
            if response and 'response' in response:
                for team_data in response['response']:
                    team = Team(
                        id=team_data['team']['id'],
                        name=team_data['team']['name'],
                        logo_url=team_data['team']['logo'],
                        league=league.id
                    )
                    existing_team = db.query(Team).filter(Team.id == team.id).first()
                    if not existing_team:
                        db.add(team)
        db.commit()
        print("Teams initialized successfully")
    except Exception as e:
        print(f"Error initializing teams: {str(e)}")
        db.rollback()

async def init_basic_player_data(db: Session):
    """Initialize basic player data for all teams"""
    try:
        teams = db.query(Team).all()
        for team in teams:
            response = await football_api.get_team_players(team.id)
            logger.info(f"Processing team {team.id} players")
            
            if response and 'response' in response:
                for squad in response['response']:
                    for player_data in squad.get('players', []):
                        logger.info(f"Raw player data: {player_data}")
                        
                        player = Player(
                            id=player_data['id'],
                            name=player_data['name'],
                            team_id=team.id,
                            position_id=get_position_id(player_data['position']),
                            country_id=player_data.get('nationality', {}).get('id'),
                            birth_date=datetime.strptime(player_data.get('birth', {}).get('date', ''), '%Y-%m-%d').date() if player_data.get('birth', {}).get('date') else None
                        )
                        
                        existing_player = db.query(Player).filter(Player.id == player.id).first()
                        if not existing_player:
                            db.add(player)
                            logger.info(f"Added player: {player.name} with country_id: {player.country_id} and birth_date: {player.birth_date}")
                
                db.commit()
                logger.info(f"Committed players for team {team.id}")
                
    except Exception as e:
        logger.error(f"Error initializing players: {str(e)}")
        db.rollback()

async def initialize_database():
    print("Starting database initialization...")
    create_tables()
    
    db = SessionLocal()
    try:
        # 1. Initialize positions (most basic static data)
        init_positions(db)
        db.commit()
        print("Positions initialized")
        
        # 2. Initialize countries
        await init_countries(db)
        db.commit()
        print("Countries initialized")
        
        # 3. Initialize leagues
        await init_leagues(db)
        db.commit()
        print("Leagues initialized")
        
        # 4. Initialize teams
        await init_teams(db)
        db.commit()
        print("Teams initialized")
        
        # 5. Initialize players (depends on teams and positions)
        await init_basic_player_data(db)
        db.commit()
        print("Players initialized")
        
        print("Database initialization completed successfully")
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(initialize_database()) 