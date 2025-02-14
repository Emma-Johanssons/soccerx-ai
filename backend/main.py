from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import matches, leagues, teams, players, search, standings

from app.database import engine, Base, create_tables
from app.sql_models import models

app = FastAPI(title="SoccerX Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_tables()

app.include_router(matches.router, prefix="/api/matches")
app.include_router(leagues.router, prefix="/api/leagues")
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(standings.router, prefix="/api/standings", tags=["standings"]) 
app.include_router(players.router, prefix="/api/players", tags=["players"])