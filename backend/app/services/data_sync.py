from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League, LastSync, Country
import logging

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
            
        response = self.football_api.get_leagues()
        if response and 'response' in response:
            for league_data in response['response']:
                league = League(
                    id=league_data['league']['id'],
                    name=league_data['league']['name'],
                    country=league_data['country']['name'],
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

    def sync_all(self):
        try:
            self.sync_countries()
            self.sync_leagues()
            self.sync_teams()
            logger.info("All data synced successfully")
        except Exception as e:
            logger.error(f"Error during sync: {str(e)}")
            self.db.rollback()
            raise e