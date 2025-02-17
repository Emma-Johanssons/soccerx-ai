from pydantic import BaseModel
from datetime import datetime, date, time
from typing import Optional, List

#User Schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

#Team Schemas
class TeamBase(BaseModel):
    name:str
    league:str
    country_id: Optional[int]
    logo_url: Optional[str]
    founded_year: Optional[int]
    stadium_name: Optional[str]
    team_manager: Optional[str]

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id:int
    class Config:
        from_attributes = True

#Player Schemas
class PlayerBase(BaseModel):
    name: str
    position_id: str
    team_id: int
    country_id: int
    birth_date: date

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    class Config:
        from_attributes = True

#Match Schemas
class MatchBase(BaseModel):
    home_team_id: int
    away_team_id: int
    date: datetime
    match_status_id: int
    score_home: Optional[int] = None
    score_away: Optional[int] = None
    stadium: Optional[str]
    referee: Optional[str]

class MatchCreate(MatchBase):
    pass

class Match(MatchBase):
    id:int
    class Config:
        from_attributes = True

#MatchStatus Schemas
class MatchStatusBase(BaseModel):
    status: str

class MatchStatusCreate(MatchStatusBase):
    pass 

class MatchStatus(MatchStatusBase):
    id: int
    class Config:
        from_attributes = True

#MatchEvent Schemas
class MatchEventBase(BaseModel):
    match_id: int
    player_id: int
    event_type_id: int
    minute: time
    description: Optional[str]

class MatchEventCreate(MatchEventBase):
    pass 

class MatchEvent(MatchEventBase):
    id: int
    class Config:
        from_attributes = True

#EventType Schemas
class EventTypeBase(BaseModel):
    event: str

class EventTypeCreate(EventTypeBase):
    pass 

class EventType(EventTypeBase):
    id: int
    class Config:
        from_attributes = True

#MatchStatistics Schemas
class MatchStatisticsBase(BaseModel):
    match_id: int
    team_id: int
    possession: int
    shots: int
    corners: int
    fouls: int

class MatchStatisticsCreate(MatchStatisticsBase):
    pass 

class MatchStatistic(MatchStatisticsBase):
    id: int
    class Config:
        from_attributes = True

#PlayerMatchStatistic Schemas
class PlayerMatchStatisticBase(BaseModel):
    player_id: int
    match_id: int
    team_id: int
    minutes_played: int
    goals: int
    assists: int
    shots: int
    passes: int

class PlayerMatchStatisticCreate(PlayerMatchStatisticBase):
    pass

class PlayerMatchStatistic(PlayerMatchStatisticBase):
    id: int
    class Config:
        from_attributes = True

#UserPreference Schema
class UserPreferenceBase(BaseModel):
    user_id: int
    team_id: Optional[int]
    preferred_leagues: Optional[str]
    display_timezone: Optional[time]

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreference(UserPreferenceBase):
    id: int
    class Config:
        from_attributes = True

#Country Schemas
class CountryBase(BaseModel):
    country_name: str

class CountryCreate(CountryBase):
    pass 

class Country(CountryBase):
    id: int
    class Config:
        from_attributes = True

#League Schemas
class LeagueBase(BaseModel):
    name: str

class LeagueCreate(LeagueBase):
    pass 

class League(LeagueBase):
    id: int
    class Config:
        from_attributes = True

#Position Schemas
class PositionBase(BaseModel):
    positions: str

class PositionCreate(PositionBase):
    pass 

class Position(PositionBase):
    id: int
    class Config:
        from_attributes = True
    

# Response Schemas
class ResponseBase(BaseModel):
    status: str
    message: str

class TeamResponse(ResponseBase):
    data: List[Team]

class PlayerResponse(ResponseBase):
    data: List[Player]

class MatchResponse(ResponseBase):
    data: List[Match]

class MatchStatusResponse(ResponseBase):
    data: List[MatchStatus]

class MatchEventResponse(ResponseBase):
    data: List[MatchEvent]

class EventTypeResponse(ResponseBase):
    data: List[EventType]

class MatchStatisticResponse(ResponseBase):
    data: List[MatchStatistic]

class PlayerMatchStatisticResponse(ResponseBase):
    data: List[PlayerMatchStatistic]

class UserPreferenceResponse(ResponseBase):
    data: List[UserPreference]

class CountryResponse(ResponseBase):
    data: List[Country]

class LeagueResponse(ResponseBase):
    data: List[League]

class PositionResponse(ResponseBase):
    data: List[Position]