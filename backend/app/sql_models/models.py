from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, Time, Float, Boolean
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime, timedelta



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
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"))
    founded = Column(Integer)
    national = Column(Boolean)
    logo_url = Column(String)  # Changed from logo to logo_url
    venue_name = Column(String)  # Add this field
    venue_capacity = Column(Integer)  # Add this field
    venue_id = Column(Integer, ForeignKey("venues.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="teams")
    venue = relationship("Venue", back_populates="teams")
    league = relationship("League", back_populates="teams")
    players = relationship("Player", back_populates="team")
    home_matches = relationship("Match", back_populates="home_team", foreign_keys="Match.home_team_id")
    away_matches = relationship("Match", back_populates="away_team", foreign_keys="Match.away_team_id")
    match_statistics = relationship("MatchStatistic", back_populates="team")
    statistics = relationship("TeamStatistics", back_populates="team")
    events = relationship("MatchEvent", back_populates="team")
    player_statistics = relationship("PlayerStatistics", back_populates="team")
    standings = relationship("Standing", back_populates="team")

    def is_stale(self) -> bool:
        """Check if team data is older than 24 hours"""
        if not self.last_updated:
            return True
        stale_threshold = datetime.utcnow() - timedelta(hours=24)
        return self.last_updated < stale_threshold

class Player(Base):
    __tablename__ = "players"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    firstname = Column(String)
    lastname = Column(String)
    age = Column(Integer)
    nationality = Column(String)
    height = Column(String)
    weight = Column(String)
    injured = Column(Boolean)
    jersey_number = Column(Integer)
    photo_url = Column(String)
    team_id = Column(Integer, ForeignKey("teams.id"))
    country_id = Column(Integer, ForeignKey("countries.id"))
    position_id = Column(Integer, ForeignKey("positions.id"))
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="players")
    country = relationship("Country", back_populates="players")
    position = relationship("Position", back_populates="players")
    statistics = relationship("PlayerStatistics", back_populates="player")
    match_statistics = relationship("PlayerMatchStatistic", back_populates="player")
    events = relationship(
        "MatchEvent",
        primaryjoin="and_(MatchEvent.player_id==Player.id)",
        back_populates="player",
        foreign_keys="[MatchEvent.player_id]"
    )
    assisted_events = relationship(
        "MatchEvent",
        primaryjoin="and_(MatchEvent.assist_player_id==Player.id)",
        foreign_keys="[MatchEvent.assist_player_id]"
    )

class MatchStatus(Base):
    __tablename__ = "match_statuses"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)
    elapsed = Column(Integer)
    
    # Relationships
    matches = relationship("Match", back_populates="status")

class Match(Base):
    __tablename__ = "matches"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    api_match_id = Column(Integer, unique=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"))
    away_team_id = Column(Integer, ForeignKey("teams.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    date = Column(DateTime)
    match_status_id = Column(Integer, ForeignKey("match_statuses.id"))
    score_home = Column(Integer)
    score_away = Column(Integer)
    stadium = Column(String)
    referee = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="matches")
    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    status = relationship("MatchStatus", back_populates="matches")
    events = relationship("MatchEvent", back_populates="match")
    statistics = relationship("MatchStatistic", back_populates="match")
    player_statistics = relationship("PlayerMatchStatistic", back_populates="match")

    def is_stale(self) -> bool:
        """Check if match data is older than 5 minutes"""
        if not self.last_updated:
            return True
        stale_threshold = datetime.utcnow() - timedelta(minutes=5)
        return self.last_updated < stale_threshold

    def to_dict(self):
        """Convert match to dictionary"""
        return {
            "id": self.id,
            "api_match_id": self.api_match_id,
            "date": self.date.isoformat() if self.date else None,
            "stadium": self.stadium,
            "referee": self.referee,
            "home_team": self.home_team.name if self.home_team else None,
            "away_team": self.away_team.name if self.away_team else None,
            "league": self.league.name if self.league else None,
            "status": self.status.code if self.status else None,
            "score_home": self.score_home,
            "score_away": self.score_away,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }

class MatchEvent(Base):
    __tablename__ = "match_events"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    assist_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    event_type_id = Column(Integer, ForeignKey("event_types.id"))
    type = Column(String)
    time = Column(Integer)
    details = Column(String, nullable=True)
    
    # Relationships
    match = relationship("Match", back_populates="events")
    team = relationship("Team", back_populates="events")
    player = relationship(
        "Player",
        primaryjoin="and_(MatchEvent.player_id==Player.id)",
        back_populates="events",
        foreign_keys=[player_id]
    )
    assist_player = relationship(
        "Player",
        primaryjoin="and_(MatchEvent.assist_player_id==Player.id)",
        foreign_keys=[assist_player_id]
    )
    event_type = relationship("EventType", back_populates="events")

class EventType(Base):
    __tablename__ = "event_types"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    events = relationship("MatchEvent", back_populates="event_type")




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
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    country_name = Column(String)
    code = Column(String)
    flag = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    leagues = relationship("League", back_populates="country")
    teams = relationship("Team", back_populates="country")
    players = relationship("Player", back_populates="country")

class League(Base):
    __tablename__ = "leagues"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    type = Column(String)
    country_id = Column(Integer, ForeignKey("countries.id"))
    logo = Column(String)
    flag = Column(String)
    season = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    country = relationship("Country", back_populates="leagues")
    teams = relationship("Team", back_populates="league")
    matches = relationship("Match", back_populates="league")
    team_statistics = relationship("TeamStatistics", back_populates="league")
    player_statistics = relationship("PlayerStatistics", back_populates="league")
    standings = relationship("Standing", back_populates="league")

class Standing(Base):
    __tablename__ = "standings"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    league_id = Column(Integer, ForeignKey("leagues.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    season = Column(Integer)
    rank = Column(Integer)
    points = Column(Integer)
    played = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals_for = Column(Integer)
    goals_against = Column(Integer)
    goal_difference = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    league = relationship("League", back_populates="standings")
    team = relationship("Team", back_populates="standings")

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    code = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    players = relationship("Player", back_populates="position")

class LastSync(Base):
    __tablename__ = "last_sync"
    
    id = Column(Integer, primary_key=True)
    sync_type = Column(String)  # 'leagues', 'teams', 'players'
    last_sync_time = Column(DateTime, default=datetime.now)

class TeamStatistics(Base):
    __tablename__ = "team_statistics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    season = Column(Integer)
    matches_played = Column(Integer)
    wins = Column(Integer)
    draws = Column(Integer)
    losses = Column(Integer)
    goals_for = Column(Integer)
    goals_against = Column(Integer)
    clean_sheets = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="statistics")
    league = relationship("League", back_populates="team_statistics")

class PlayerStatistics(Base):
    __tablename__ = "player_statistics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    league_id = Column(Integer, ForeignKey("leagues.id"))
    season = Column(Integer)
    appearances = Column(Integer)
    minutes_played = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    player = relationship("Player", back_populates="statistics")
    team = relationship("Team", back_populates="player_statistics")
    league = relationship("League", back_populates="player_statistics")

class MatchStatistic(Base):
    __tablename__ = "match_statistics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    shots_on_goal = Column(Integer)
    shots_off_goal = Column(Integer)
    total_shots = Column(Integer)
    blocked_shots = Column(Integer)
    shots_inside_box = Column(Integer)
    shots_outside_box = Column(Integer)
    fouls = Column(Integer)
    corner_kicks = Column(Integer)
    offsides = Column(Integer)
    ball_possession = Column(Float)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    saves = Column(Integer)
    total_passes = Column(Integer)
    passes_accurate = Column(Integer)
    passes_percentage = Column(Float)
    
    # Relationships
    match = relationship("Match", back_populates="statistics")
    team = relationship("Team", back_populates="match_statistics")

class PlayerMatchStatistic(Base):
    __tablename__ = "player_match_statistics"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    minutes_played = Column(Integer)
    rating = Column(Float)
    shots_total = Column(Integer)
    shots_on_goal = Column(Integer)
    goals = Column(Integer)
    assists = Column(Integer)
    passes_total = Column(Integer)
    passes_accuracy = Column(Float)
    
    # Relationships
    match = relationship("Match", back_populates="player_statistics")
    player = relationship("Player", back_populates="match_statistics")

class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    city = Column(String)
    capacity = Column(Integer)
    surface = Column(String)
    image = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    teams = relationship("Team", back_populates="venue")