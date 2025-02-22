from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League, LastSync, Country, TeamStatistics, PlayerStatistics
import logging
from ..database import Base, engine

logger = logging.getLogger(__name__)

class DataSyncService:
    def __init__(self, db: Session, football_api: FootballAPIService):
        self.db = db
        self.football_api = football_api
        self.major_leagues = self.football_api.major_leagues

    def should_sync(self, sync_type: str) -> bool:
        last_sync = self.db.query(LastSync).filter(LastSync.sync_type == sync_type).first()
        if not last_sync:
            return True
        return datetime.now() - last_sync.last_sync_time > timedelta(days=1)

    def update_sync_time(self, sync_type: str):
        last_sync = self.db.query(LastSync).filter(LastSync.sync_type == sync_type).first()
        if last_sync:
            last_sync.last_sync_time = datetime.now()
        else:
            self.db.add(LastSync(sync_type=sync_type))
        self.db.commit()

    def sync_countries(self):
        if not self.should_sync('countries'):
            return
        
        response = self.football_api.get_countries()
        if response and 'response' in response:
            for country_data in response['response']:
                country = Country(
                    id=country_data.get('id'),
                    country_name=country_data.get('name')
                )
                existing = self.db.query(Country).filter(Country.id == country.id).first()
                if existing:
                    existing.country_name = country.country_name
                else:
                    self.db.add(country)
            
            self.db.commit()
            self.update_sync_time('countries')
            logger.info("Countries synced successfully")

    def sync_leagues(self):
        if not self.should_sync('leagues'):
            return
        
        # Get country mapping first
        country_map = {}
        countries = self.db.query(Country).all()
        for country in countries:
            country_map[country.country_name] = country.id

        response = self.football_api.get_leagues()
        if response and 'response' in response:
            for league_data in response['response']:
                country_name = league_data['country']['name']
                country_id = country_map.get(country_name)
                
                if country_id:  # Only add league if we have a valid country_id
                    league = League(
                        id=league_data['league']['id'],
                        name=league_data['league']['name'],
                        country_id=country_id,  # Use country_id instead of country name
                        logo=league_data['league'].get('logo')
                    )
                    existing = self.db.query(League).filter(League.id == league.id).first()
                    if existing:
                        for key, value in league.__dict__.items():
                            if not key.startswith('_'):
                                setattr(existing, key, value)
                    else:
                        self.db.add(league)
        
            self.db.commit()
            self.update_sync_time('leagues')
            logger.info("Leagues synced successfully")

    def sync_teams(self):
        logger.info("Syncing teams...")
        if not self.should_sync('teams'):
            return

        # Get country mapping first
        country_map = {}
        countries = self.db.query(Country).all()
        for country in countries:
            country_map[country.country_name] = country.id

        for league_name, league_info in self.major_leagues.items():
            logger.info(f"Syncing teams for {league_name} with ID {league_info['id']}")
            try:
                response = self.football_api.get_teams(league_info['id'], league_info['season'])
                logger.info(f"Found {len(response.get('response', []))} teams for {league_name}")
                
                if response and 'response' in response:
                    for team_data in response['response']:
                        try:
                            country_name = team_data['team'].get('country')
                            country_id = country_map.get(country_name)
                            
                            team = Team(
                                id=team_data['team']['id'],
                                name=team_data['team']['name'],
                                logo_url=team_data['team'].get('logo'),
                                country_id=country_id,  # Use the ID instead of name
                                founded=team_data['team'].get('founded'),
                                venue_name=team_data['venue'].get('name'),
                                venue_capacity=team_data['venue'].get('capacity'),
                                league=league_info['id']
                            )
                            existing = self.db.query(Team).filter(Team.id == team.id).first()
                            if existing:
                                for key, value in team.__dict__.items():
                                    if not key.startswith('_'):
                                        setattr(existing, key, value)
                            else:
                                self.db.add(team)
                            logger.info(f"Processed team: {team.name}")
                        except Exception as e:
                            logger.error(f"Error processing team data: {e}")
                            continue
                    
                    try:
                        self.db.commit()
                        logger.info(f"Teams for league {league_name} synced successfully")
                    except Exception as e:
                        self.db.rollback()
                        logger.error(f"Error committing teams: {str(e)}")
                        continue
                else:
                    logger.error(f"No response data for league {league_name}")
                
            except Exception as e:
                logger.error(f"Error syncing teams for league {league_name}: {str(e)}")
                continue
        
        self.update_sync_time('teams')

    def fetch_and_store_team_statistics(self, team_id: int):
        """Fetch and store team statistics"""
        try:
            # Check if we have recent statistics
            recent_stats = (
                self.db.query(TeamStatistics)
                .filter(
                    TeamStatistics.team_id == team_id,
                    TeamStatistics.last_updated > datetime.now() - timedelta(hours=24)
                )
                .first()
            )
            
            if recent_stats:
                return recent_stats
            
            # Fetch new statistics from API
            stats_data = self.football_api.get_team_statistics(team_id)
            if not stats_data:
                return None
            
            # Create or update statistics
            stats = TeamStatistics(
                team_id=team_id,
                # Add other fields based on your model
                last_updated=datetime.now()
            )
            
            self.db.add(stats)
            self.db.commit()
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching team statistics: {str(e)}")
            self.db.rollback()
            return None

    async def fetch_and_store_player_statistics(self, player_id: int):
        """Similar to team statistics but for players"""
        # Implementation similar to team statistics
        pass

    async def sync_all(self):
        """Sync all data"""
        try:
            # Create tables if they don't exist
            Base.metadata.create_all(bind=engine)
            
            # Then proceed with sync
            self.sync_countries()
            self.sync_leagues()
            self.sync_teams()
            logger.info("All data synced successfully")
        except Exception as e:
            logger.error(f"Error during sync_all: {e}")
            raise