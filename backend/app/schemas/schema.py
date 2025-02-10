from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

#Team Schemas
class TeamBase(BaseModel):
    name:str
    league:str

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id:int
    class Config:
        from_attributes = True

#Player Schemas
class PlayerBase(BaseModel):
    name: str
    position: str
    team_id: int

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
    status: str
    score_home: Optional[int] = None
    score_away: Optional[int] = None

class MatchCreate(MatchBase):
    pass

class Match(MatchBase):
    id:int
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