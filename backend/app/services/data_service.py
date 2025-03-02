from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League
from ..tasks import sync_statistics
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, db: Session):
        self.db = db
        self.api = FootballAPIService()

    def get_team_data(self, team_id: int) -> dict:
        """Get team data from database or API"""
        try:
            # First try to get from database
            team = self.db.query(Team).filter(Team.id == team_id).first()
            
            if not team:
                # If not in database, fetch from API
                team_data = self.api.get_team(team_id)
                if team_data and team_data.get('response'):
                    return team_data['response'][0]
                raise HTTPException(status_code=404, detail="Team not found")
            
            return {
                "team": {
                    "id": team.id,
                    "name": team.name,
                    "code": team.code,
                    "country": team.country,
                    "founded": team.founded,
                    "national": team.national,
                    "logo": team.logo_url
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching team data: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_team(self, team_id: int):
        """Get team data, prioritizing database"""
        # Try database first
        team = self.db.query(Team).filter(Team.id == team_id).first()
        
        if team:
            # Check if data is stale (older than 24 hours)
            if team.is_stale():
                # Trigger background update
                sync_statistics.delay(team_id=team_id)
            return team
            
        # If not in database, fetch from API
        try:
            team_data = await self.api.get_team(team_id)
            if team_data:
                team = Team(**team_data)
                self.db.add(team)
                self.db.commit()
                # Trigger background task to fetch detailed stats
                sync_statistics.delay(team_id=team_id)
                return team
        except Exception as e:
            logger.error(f"Error fetching team data: {e}")
            raise 