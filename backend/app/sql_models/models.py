from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime, timedelta
from sqlalchemy.orm import Session



class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime)
    preferences = relationship("UserPreference", back_populates="user")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    code = Column(String, nullable=True)
    logo_url = Column(String)
    founded = Column(Integer)
    venue_name = Column(String)
    venue_capacity = Column(Integer)
    league = Column(Integer, ForeignKey("leagues.id"))
    country_id = Column(Integer, ForeignKey("countries.id"))
    stadium_name = Column(String)
    team_manager = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    players = relationship("Player", back_populates="team")
    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
    country = relationship("Country", back_populates="teams")

    def to_dict(self):
        """Convert team to dictionary format"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "logo": self.logo_url,
            "founded": self.founded,
            "venue": {
                "name": self.venue_name,
                "capacity": self.venue_capacity
            }
        }

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    position_id = Column(Integer, ForeignKey("positions.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    country_id = Column(Integer, ForeignKey("countries.id"))
    birth_date = Column(Date)
    
    team = relationship("Team", back_populates="players")
    country = relationship("Country", back_populates="players")
    position = relationship("Position", back_populates="players")
    match_statistics = relationship("PlayerMatchStatistic", back_populates="player")
    match_events = relationship("MatchEvent", back_populates="player")

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    date = Column(DateTime)
    match_status_id = Column(Integer, ForeignKey("match_statuses.id"))
    score_home = Column(Integer)
    score_away = Column(Integer)
    stadium = Column(String)
    referee = Column(String)
    
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    status = relationship("MatchStatus", back_populates="matches")
    events = relationship("MatchEvent", back_populates="match")
    statistics = relationship("MatchStatistic", back_populates="match")
    player_statistics = relationship("PlayerMatchStatistic", back_populates="match")

class MatchStatus(Base):
    __tablename__ = "match_statuses"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    matches = relationship("Match", back_populates="status")

class MatchEvent(Base):
    __tablename__ = "match_events"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    event_type_id = Column(Integer, ForeignKey("event_types.id"))
    minute = Column(Time)
    description = Column(String)
    
    match = relationship("Match", back_populates="events")
    player = relationship("Player", back_populates="match_events")
    event_type = relationship("EventType", back_populates="events")

class EventType(Base):
    __tablename__ = "event_types"
    
    id = Column(Integer, primary_key=True, index=True)
    event = Column(String)
    events = relationship("MatchEvent", back_populates="event_type")

class MatchStatistic(Base):
    __tablename__ = "match_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    possession = Column(Integer)
    shots = Column(Integer)
    corners = Column(Integer)
    fouls = Column(Integer)
    
    match = relationship("Match", back_populates="statistics")
    team = relationship("Team")

class PlayerMatchStatistic(Base):
    __tablename__ = "player_match_statistics"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    minutes_played = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    shots = Column(Integer)
    passes = Column(Integer)
    
    player = relationship("Player", back_populates="match_statistics")
    match = relationship("Match", back_populates="player_statistics")
    team = relationship("Team")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    preferred_leagues = Column(String)
    display_timezone = Column(Time)
    
    user = relationship("User", back_populates="preferences")
    team = relationship("Team")

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True, index=True)
    country_name = Column(String, nullable=False)
    teams = relationship("Team", back_populates="country")
    players = relationship("Player", back_populates="country")
    leagues = relationship("League", back_populates="country")

class League(Base):
    __tablename__ = "leagues"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"))
    logo = Column(String, nullable=True)
    type = Column(String, nullable=True)
    
    country = relationship("Country", back_populates="leagues")

    def to_dict(self):
        """Convert league to dictionary format"""
        return {
            "id": self.id,
            "name": self.name,
            "type": getattr(self, 'type', "League") if hasattr(self, 'type') else "League",
            "logo": self.logo,
            "country": self.country.country_name if self.country else None
        }

class Position(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) 
    code = Column(String, nullable=True)
    positions = Column(String)
    players = relationship("Player", back_populates="position")

class LastSync(Base):
    __tablename__ = "last_sync"
    
    id = Column(Integer, primary_key=True)
    sync_type = Column(String)  # 'leagues', 'teams', 'players'
    last_sync_time = Column(DateTime, default=datetime.now)

class TeamStatistics(Base):
    __tablename__ = "team_statistics"
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(Integer)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    matches_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)
    form = Column(JSON, default=list)
    last_updated = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", backref="statistics")
    league = relationship("League")

    def to_dict(self):
        """Convert team statistics to dictionary format"""
        return {
            "team_id": self.team_id,
            "season": self.season,
            "league_id": self.league_id,
            "matches_played": self.matches_played,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "clean_sheets": self.clean_sheets,
            "last_updated": self.last_updated.isoformat()
        }

class PlayerStatistics(Base):
    __tablename__ = "player_statistics"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    season = Column(Integer)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    appearances = Column(Integer)
    minutes_played = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

    player = relationship("Player", backref="statistics")
    league = relationship("League")

class LeagueStandings(Base):
    __tablename__ = "league_standings"
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    data = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    league = relationship("League", backref="standings")

    def to_dict(self):
        """Convert standings to dictionary format"""
        return {
            "id": self.id,
            "league_id": self.league_id,
            "data": self.data,
            "last_updated": self.last_updated.isoformat()
        }