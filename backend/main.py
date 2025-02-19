import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import teams, players, matches, leagues, search, standings
from app.database import recreate_tables, SessionLocal
from app.services.background_tasks import scheduler, schedule_data_sync
from app.services.data_sync import DataSyncService
from app.api_service.football_api import FootballAPIService

def initial_data_load():
    """Load initial data into the database"""
    logger.info("Starting initial data load...")
    db = SessionLocal()
    try:
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        sync_service.sync_all()  # This will populate all tables
        logger.info("Initial data load completed successfully")
    except Exception as e:
        logger.error(f"Error loading initial data: {e}")
        raise
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Recreate tables
    recreate_tables()
    
    # Load initial data
    initial_data_load()
    
    # Schedule future updates
    schedule_data_sync()
    
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(leagues.router, prefix="/api/leagues", tags=["leagues"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(standings.router, prefix="/api/standings", tags=["standings"])