from sqlalchemy.orm import Session
from .database import engine, SessionLocal, create_tables
from .api_service.football_api import FootballAPIService
from .sql_models.models import Country, League, Position
import asyncio

football_api = FootballAPIService()

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
    # Static positions data
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
        db.commit()
        print("Positions initialized successfully")
    except Exception as e:
        print(f"Error initializing positions: {str(e)}")
        db.rollback()

async def initialize_database():
    print("Starting database initialization...")
    create_tables()
    
    db = SessionLocal()
    try:
        # Initialize static data
        await init_countries(db)
        await init_leagues(db)
        init_positions(db)
        
        print("Database initialization completed")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(initialize_database()) 