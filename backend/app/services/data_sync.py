from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League, LastSync, Country, TeamStatistics, PlayerStatistics, Position, MatchStatistic, Match, MatchStatus
from ..utils.position_mapper import get_position_id
import logging
from ..database import Base, engine

logger = logging.getLogger(__name__)

def initialize_match_statuses(db: Session):
    """Initialize match statuses in the database"""
    try:
        statuses = [
            {"id": 1, "name": "Not Started", "code": "NS"},
            {"id": 2, "name": "First Half", "code": "1H"},
            {"id": 3, "name": "Half Time", "code": "HT"},
            {"id": 4, "name": "Second Half", "code": "2H"},
            {"id": 5, "name": "Extra Time", "code": "ET"},
            {"id": 6, "name": "Penalty", "code": "P"},
            {"id": 7, "name": "Full Time", "code": "FT"},
            {"id": 8, "name": "After Extra Time", "code": "AET"},
            {"id": 9, "name": "Penalties", "code": "PEN"},
            {"id": 10, "name": "Break Time", "code": "BT"},
            {"id": 11, "name": "Suspended", "code": "SUSP"},
            {"id": 12, "name": "Interrupted", "code": "INT"},
            {"id": 13, "name": "Postponed", "code": "PST"},
            {"id": 14, "name": "Cancelled", "code": "CANC"},
            {"id": 15, "name": "Abandoned", "code": "ABD"},
            {"id": 16, "name": "Technical Loss", "code": "AWD"},
            {"id": 17, "name": "Walk Over", "code": "WO"},
            {"id": 18, "name": "Live", "code": "LIVE"}
        ]
        
        for status in statuses:
            existing = db.query(MatchStatus).filter(MatchStatus.id == status['id']).first()
            if not existing:
                db.add(MatchStatus(**status))
        
        db.commit()
        logger.info("Match statuses initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing match statuses: {str(e)}")
        db.rollback()
        raise

class DataSyncService:
    def __init__(self, db: Session, football_api: FootballAPIService):
        self.db = db
        self.football_api = football_api
        self.major_leagues = self.football_api.major_leagues

    def should_sync(self, sync_type: str) -> bool:
        """Check if we should sync based on last sync time"""
        last_sync = self.db.query(LastSync).filter(LastSync.sync_type == sync_type).first()
        if not last_sync:
            # If no last sync record exists, check if we have any data
            if sync_type == 'countries':
                has_data = self.db.query(Country).first() is not None
            elif sync_type == 'leagues':
                has_data = self.db.query(League).first() is not None
            elif sync_type == 'teams':
                has_data = self.db.query(Team).first() is not None
            elif sync_type == 'positions':
                has_data = self.db.query(Position).first() is not None
            elif sync_type == 'players':
                has_data = self.db.query(Player).first() is not None
            else:
                has_data = False
                
            # If we have data but no sync record, create one
            if has_data:
                self.update_sync_time(sync_type)
                return False
            return True
            
        return datetime.now() - last_sync.last_sync_time > timedelta(days=1)

    def update_sync_time(self, sync_type: str):
        """Update the last sync time for a given sync type"""
        try:
            last_sync = self.db.query(LastSync).filter(LastSync.sync_type == sync_type).first()
            current_time = datetime.now()
            
            if last_sync:
                last_sync.last_sync_time = current_time
                logger.info(f"Updated last sync time for {sync_type} to {current_time}")
            else:
                new_sync = LastSync(sync_type=sync_type, last_sync_time=current_time)
                self.db.add(new_sync)
                logger.info(f"Created new sync record for {sync_type} with time {current_time}")
            
            self.db.commit()
        except Exception as e:
            logger.error(f"Error updating sync time for {sync_type}: {str(e)}")
            self.db.rollback()

    def sync_countries(self):
        """Update country data if needed"""
        if not self.should_sync('countries'):
            logger.info("Countries sync skipped - recent sync exists")
            return
        
        logger.info("Starting countries sync")
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
                                league_id=league_info['id']
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

    def sync_positions(self):
        """Sync player positions"""
        logger.info("Starting positions sync")
        try:
            # Check if positions already exist
            existing_count = self.db.query(Position).count()
            
            if existing_count == 0:
                # Default positions
                positions = [
                    Position(name="Goalkeeper", code="GK"),
                    Position(name="Defender", code="D"),
                    Position(name="Midfielder", code="M"),
                    Position(name="Attacker", code="F")
                ]
                self.db.add_all(positions)
                self.db.commit()
                logger.info(f"Added {len(positions)} positions")
            else:
                logger.info(f"Positions already exist ({existing_count} records)")
        except Exception as e:
            logger.error(f"Error syncing positions: {e}")
            self.db.rollback()
            raise

    def sync_players(self):
        """Update player data if needed"""
        if not self.should_sync('players'):
            logger.info("Players sync skipped - recent sync exists")
            return

        logger.info("Starting players sync")
        try:
            current_season = 2024
            
            teams = self.db.query(Team).all()
            for team in teams:
                try:
                    response = self.football_api.get_team_squad(team.id, season=current_season)
                    if response and 'response' in response and response['response']:
                        # The squad data is nested in response[0]['players']
                        squad_data = response['response'][0].get('players', [])
                        
                        for player_data in squad_data:
                            try:
                                if not player_data:
                                    logger.warning(f"Empty player data for team {team.name}")
                                    continue
                                    
                                player = Player(
                                    id=player_data.get('id'),  # Use get() to avoid KeyError
                                    name=player_data.get('name'),
                                    team_id=team.id,
                                    position_id=get_position_id(player_data.get('position', 'Unknown'))
                                )
                                
                                if not player.id:
                                    logger.warning(f"No player ID found in data for team {team.name}")
                                    continue
                                    
                                existing = self.db.query(Player).filter(Player.id == player.id).first()
                                if existing:
                                    for key, value in player.__dict__.items():
                                        if not key.startswith('_') and value is not None:
                                            setattr(existing, key, value)
                                else:
                                    self.db.add(player)
                                    logger.info(f"Added player: {player.name} for team {team.name}")
                                    
                            except Exception as e:
                                logger.error(f"Error processing individual player for team {team.name}: {str(e)}")
                                continue
                                
                        try:
                            self.db.commit()
                            logger.info(f"Successfully synced players for team {team.name}")
                        except Exception as e:
                            logger.error(f"Error committing players for team {team.name}: {str(e)}")
                            self.db.rollback()
                    else:
                        logger.warning(f"No valid response data for team {team.name}")
                            
                except Exception as e:
                    logger.error(f"Error fetching players for team {team.name}: {str(e)}")
                    continue
            
            self.update_sync_time('players')
            logger.info("Players sync completed")
        except Exception as e:
            logger.error(f"Error in player sync process: {str(e)}")
            self.db.rollback()

    async def sync_match_statistics(self):
        """Sync match statistics for all matches in the database"""
        try:
            # Get all matches that need statistics
            matches = self.db.query(Match).all()
            for match in matches:
                try:
                    stats = await self.football_api.get_match_statistics(match.id)
                    if stats:
                        # First, remove existing statistics for this match
                        self.db.query(MatchStatistic).filter(
                            MatchStatistic.match_id == match.id
                        ).delete()
                        
                        for stat_data in stats.get('response', []):
                            match_stat = MatchStatistic(
                                match_id=match.id,
                                team_id=stat_data['team']['id'],
                                shots_on_goal=stat_data.get('shots', {}).get('on'),
                                shots_off_goal=stat_data.get('shots', {}).get('off'),
                                total_shots=stat_data.get('shots', {}).get('total'),
                                possession=stat_data.get('possession'),
                                passes=stat_data.get('passes', {}).get('total'),
                                pass_accuracy=stat_data.get('passes', {}).get('accuracy'),
                                fouls=stat_data.get('fouls'),
                                yellow_cards=stat_data.get('cards', {}).get('yellow'),
                                red_cards=stat_data.get('cards', {}).get('red'),
                                offsides=stat_data.get('offsides'),
                                corners=stat_data.get('corners'),
                                last_updated=datetime.utcnow()
                            )
                            self.db.add(match_stat)
                        self.db.commit()
                except Exception as e:
                    logger.error(f"Error syncing statistics for match {match.id}: {e}")
                    self.db.rollback()
                    continue
        except Exception as e:
            logger.error(f"Error syncing match statistics: {e}")
            self.db.rollback()
            raise

    async def sync_all(self):
        """Sync all data"""
        logger.info("Starting full data sync...")
        try:
            self.sync_positions()
            self.sync_countries()
            self.sync_leagues()
            self.sync_teams()
            await self.sync_match_statistics()
            logger.info("Full data sync completed")
        except Exception as e:
            logger.error(f"Error during sync_all: {e}")
            raise

# Make sure initialize_match_statuses is explicitly exported
__all__ = ['DataSyncService', 'initialize_match_statuses']

class DataFetchStrategy:
    def __init__(self):
        self.REFRESH_INTERVALS = {
            'static': timedelta(days=7),    # Team info, logos, etc.
            'daily': timedelta(days=1),     # Standings, completed matches
            'frequent': timedelta(hours=4),  # Team statistics
            'live': timedelta(minutes=5)     # Live matches, scores
        }