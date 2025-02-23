from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League
from ..tasks import sync_statistics
import logging

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, db: Session):
        self.db = db
        self.api = FootballAPIService()

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