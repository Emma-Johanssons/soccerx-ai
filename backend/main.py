from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import matches

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

app.include_router(matches.router, prefix = "/api")

