import logging
import importlib
import app.tasks
importlib.reload(app.tasks)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import teams, players, matches, leagues, search, standings
from app.database import recreate_tables, SessionLocal, Base, engine
from app.database_init import initialize_database
from app.services.data_sync import DataSyncService
from app.api_service.football_api import FootballAPIService
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    redis = None
    try:
        # Create all tables first
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Then proceed with data sync
        db = SessionLocal()
        football_api = FootballAPIService()
        sync_service = DataSyncService(db, football_api)
        await sync_service.sync_all()
        logger.info("Initial data sync completed")
        
        # Initialize Redis
        redis = aioredis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        await redis.ping()  # Test connection
        FastAPICache.init(RedisBackend(redis), prefix="footystats-cache")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()
        if redis:
            await redis.close()

app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with explicit prefixes
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(players.router, prefix="/api/players", tags=["players"])
app.include_router(leagues.router, prefix="/api/leagues", tags=["leagues"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(standings.router, prefix="/api/standings", tags=["standings"])

# After registering all routes
for route in app.routes:
    logger.info(f"Registered route: {route.path}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """Initialize database and tables on startup"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize data
        db = SessionLocal()
        try:
            football_api = FootballAPIService()
            sync_service = DataSyncService(db, football_api)
            await sync_service.sync_all()
            logger.info("Initial data sync completed")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise