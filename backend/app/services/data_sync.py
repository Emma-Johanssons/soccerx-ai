from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..api_service.football_api import FootballAPIService
from ..sql_models.models import Team, Player, League, LastSync, Country, TeamStatistics, PlayerStatistics, Position, EventType, MatchStatus, Match, MatchEvent, MatchStatistic, PlayerMatchStatistic
from ..utils.position_mapper import get_position_id
import logging
from ..database import Base, engine

logger = logging.getLogger(__name__)

class DataSyncService:
    def __init__(self, db, football_api=None):
        self.db = db
        self.football_api = football_api or FootballAPIService()
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

    def sync_team_statistics(self):
        """Sync team statistics for all teams"""
        try:
            logger.info("Starting team statistics sync")
            
            # Get current season
            current_season = datetime.now().year
            if datetime.now().month < 7:
                current_season -= 1
            
            # Get all teams
            teams = self.db.query(Team).all()
            logger.info(f"Found {len(teams)} teams to sync statistics")
            
            for team in teams:
                try:
                    # Get team statistics from API
                    stats_response = self.football_api.get_team_statistics(team.id, current_season)
                    
                    if stats_response and 'response' in stats_response:
                        # Process each league's statistics
                        for league_stats in stats_response['response']:
                            try:
                                league_id = league_stats.get('league', {}).get('id')
                                if not league_id:
                                    continue
                                    
                                # Check if we already have statistics for this team/league/season
                                existing_stats = self.db.query(TeamStatistics).filter(
                                    TeamStatistics.team_id == team.id,
                                    TeamStatistics.league_id == league_id,
                                    TeamStatistics.season == current_season
                                ).first()
                                
                                if existing_stats:
                                    # Update existing statistics
                                    existing_stats.matches_played = league_stats.get('fixtures', {}).get('played', {}).get('total', 0) or 0
                                    existing_stats.wins = league_stats.get('fixtures', {}).get('wins', {}).get('total', 0) or 0
                                    existing_stats.draws = league_stats.get('fixtures', {}).get('draws', {}).get('total', 0) or 0
                                    existing_stats.losses = league_stats.get('fixtures', {}).get('loses', {}).get('total', 0) or 0
                                    existing_stats.goals_for = league_stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0) or 0
                                    existing_stats.goals_against = league_stats.get('goals', {}).get('against', {}).get('total', {}).get('total', 0) or 0
                                    existing_stats.clean_sheets = league_stats.get('clean_sheet', {}).get('total', 0) or 0
                                    existing_stats.last_updated = datetime.now()
                                else:
                                    # Create new statistics record
                                    new_stats = TeamStatistics(
                                        team_id=team.id,
                                        league_id=league_id,
                                        season=current_season,
                                        matches_played=league_stats.get('fixtures', {}).get('played', {}).get('total', 0) or 0,
                                        wins=league_stats.get('fixtures', {}).get('wins', {}).get('total', 0) or 0,
                                        draws=league_stats.get('fixtures', {}).get('draws', {}).get('total', 0) or 0,
                                        losses=league_stats.get('fixtures', {}).get('loses', {}).get('total', 0) or 0,
                                        goals_for=league_stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0) or 0,
                                        goals_against=league_stats.get('goals', {}).get('against', {}).get('total', {}).get('total', 0) or 0,
                                        clean_sheets=league_stats.get('clean_sheet', {}).get('total', 0) or 0,
                                        last_updated=datetime.now()
                                    )
                                    self.db.add(new_stats)
                                    
                                self.db.commit()
                                logger.info(f"Synced statistics for team {team.id}, league {league_id}")
                                
                            except Exception as e:
                                self.db.rollback()
                                logger.error(f"Error syncing statistics for team {team.id}, league {league_id}: {str(e)}")
                                continue
                            
                except Exception as e:
                    logger.error(f"Error syncing statistics for team {team.id}: {str(e)}")
                    continue
                
            # Update last sync time
            self.update_sync_time('team_statistics')
            logger.info("Team statistics sync completed")
            return "Team statistics sync completed"
            
        except Exception as e:
            logger.error(f"Error in sync_team_statistics: {str(e)}")
            raise

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
        """Sync positions table with default values"""
        try:
            logger.info("Starting positions sync")
            existing_count = self.db.query(Position).count()
            
            if existing_count == 0:
                default_positions = [
                    Position(id=1, name='Goalkeeper', code='GK'),
                    Position(id=2, name='Defender', code='DEF'),
                    Position(id=3, name='Midfielder', code='MID'),
                    Position(id=4, name='Attacker', code='ATT')
                ]
                
                self.db.bulk_save_objects(default_positions)
                self.db.commit()
                logger.info(f"Added {len(default_positions)} default positions")
            else:
                logger.info("Positions already exist in database")
                
        except Exception as e:
            logger.error(f"Error syncing positions: {str(e)}")
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

    def sync_event_types(self):
        """Sync event types to database"""
        logger.info("Syncing event types...")
        try:
            # Define standard event types
            event_types_data = [
                {"id": 1, "event": "Goal", "description": "Goal scored"},
                {"id": 2, "event": "Card", "description": "Card shown"},
                {"id": 3, "event": "Substitution", "description": "Player substitution"},
                {"id": 4, "event": "VAR", "description": "VAR decision"},
                {"id": 5, "event": "Penalty", "description": "Penalty awarded"},
                {"id": 6, "event": "Missed Penalty", "description": "Penalty missed"},
                {"id": 7, "event": "Own Goal", "description": "Own goal scored"},
                {"id": 8, "event": "Assist", "description": "Assist for goal"}
            ]
            
            for event_type in event_types_data:
                db_event_type = self.db.query(EventType).filter(
                    EventType.id == event_type["id"]
                ).first()
                
                if not db_event_type:
                    db_event_type = EventType(
                        id=event_type["id"],
                        event=event_type["event"],
                    )
                    self.db.add(db_event_type)
                else:
                    db_event_type.event = event_type["event"]
            
            self.db.commit()
            logger.info("Event types synced successfully")
            self.update_sync_time('event_types')
        except Exception as e:
            logger.error(f"Error syncing event types: {e}")
            self.db.rollback()
        
    def sync_match_statuses(self):
        """Sync match statuses to database"""
        logger.info("Syncing match statuses...")
        try:
            # Define standard match statuses
            match_statuses_data = [
                {"id": 1, "status": "NS", "description": "Not Started"},
                {"id": 2, "status": "1H", "description": "First Half"},
                {"id": 3, "status": "HT", "description": "Half Time"},
                {"id": 4, "status": "2H", "description": "Second Half"},
                {"id": 5, "status": "ET", "description": "Extra Time"},
                {"id": 6, "status": "P", "description": "Penalty Shootout"},
                {"id": 7, "status": "FT", "description": "Full Time"},
                {"id": 8, "status": "AET", "description": "After Extra Time"},
                {"id": 9, "status": "PEN", "description": "After Penalties"},
                {"id": 10, "status": "SUSP", "description": "Suspended"},
                {"id": 11, "status": "INT", "description": "Interrupted"},
                {"id": 12, "status": "PST", "description": "Postponed"},
                {"id": 13, "status": "CANC", "description": "Cancelled"},
                {"id": 14, "status": "ABD", "description": "Abandoned"},
                {"id": 15, "status": "AWD", "description": "Technical Loss"},
                {"id": 16, "status": "WO", "description": "Walk Over"}
            ]
            
            for status in match_statuses_data:
                db_status = self.db.query(MatchStatus).filter(
                    MatchStatus.id == status["id"]
                ).first()
                
                if not db_status:
                    db_status = MatchStatus(
                        id=status["id"],
                        status=status["status"],
                    )
                    self.db.add(db_status)
                else:
                    db_status.status = status["status"]
            
            self.db.commit()
            logger.info("Match statuses synced successfully")
            self.update_sync_time('match_statuses')
        except Exception as e:
            logger.error(f"Error syncing match statuses: {e}")
            self.db.rollback()
    
    def sync_matches(self):
        """Sync matches for all leagues"""
        logger.info("Syncing matches...")
        if not self.should_sync('matches'):
            logger.info("Matches sync skipped - recent sync exists")
            return
            
        try:
            # Get all leagues
            leagues = self.db.query(League).all()
            
            for league in leagues:
                try:
                    # Get current season
                    current_season = 2024  # You might want to get this dynamically
                    
                    # Fetch matches for this league and season
                    response = self.football_api.get_matches(league.id, current_season)
                    
                    if response and 'response' in response:
                        for match_data in response['response']:
                            try:
                                # Extract match data
                                match = Match(
                                    id=match_data['fixture']['id'],
                                    league_id=league.id,
                                    home_team_id=match_data['teams']['home']['id'],
                                    away_team_id=match_data['teams']['away']['id'],
                                    status_id=self.get_status_id(match_data['fixture']['status']['short']),
                                    match_date=match_data['fixture']['date'],
                                    venue=match_data['fixture']['venue']['name'],
                                    referee=match_data['fixture']['referee'],
                                    home_score=match_data['goals']['home'],
                                    away_score=match_data['goals']['away']
                                )
                                
                                existing = self.db.query(Match).filter(Match.id == match.id).first()
                                if existing:
                                    for key, value in match.__dict__.items():
                                        if not key.startswith('_') and value is not None:
                                            setattr(existing, key, value)
                                else:
                                    self.db.add(match)
                                
                            except Exception as e:
                                logger.error(f"Error processing match data: {e}")
                                continue
                        
                        self.db.commit()
                        logger.info(f"Matches for league {league.name} synced successfully")
                    else:
                        logger.warning(f"No valid response data for league {league.name}")
                        
                except Exception as e:
                    logger.error(f"Error fetching matches for league {league.name}: {e}")
                    self.db.rollback()
                    continue
            
            self.update_sync_time('matches')
            logger.info("Matches sync completed")
        except Exception as e:
            logger.error(f"Error in matches sync process: {e}")
            self.db.rollback()
    
    def sync_live_matches(self):
        """Sync live matches from the API"""
        try:
            logger.info("Syncing live matches...")
            
            # Get live matches
            response = self.football_api.get_matches(date="live")
            
            if not response or 'response' not in response:
                logger.info("No live matches found")
                return True
            
            # Extract all team IDs from the matches
            team_ids = set()
            for match_data in response['response']:
                team_ids.add(match_data['teams']['home']['id'])
                team_ids.add(match_data['teams']['away']['id'])
            
            # Check which teams are missing from our database
            existing_team_ids = [team.id for team in self.db.query(Team.id).all()]
            existing_team_ids = set(existing_team_ids)
            missing_team_ids = team_ids - existing_team_ids
            
            # Sync missing teams first
            if missing_team_ids:
                logger.info(f"Syncing {len(missing_team_ids)} missing teams before processing matches")
                for team_id in missing_team_ids:
                    try:
                        self._sync_single_team(team_id)
                    except Exception as e:
                        logger.error(f"Error syncing team {team_id}: {str(e)}")
            
            # Now process the matches
            matches_count = 0
            for match_data in response['response']:
                try:
                    # Check if match already exists
                    match_id = match_data['fixture']['id']
                    existing_match = self.db.query(Match).filter(Match.id == match_id).first()
                    
                    # Extract match status
                    status_short = match_data['fixture']['status']['short']
                    status_id = self.get_status_id(status_short)
                    
                    if existing_match:
                        # Update existing match
                        existing_match.match_status_id = status_id
                        existing_match.score_home = match_data['goals']['home']
                        existing_match.score_away = match_data['goals']['away']
                    else:
                        # Create new match
                        new_match = Match(
                            id=match_id,
                            home_team_id=match_data['teams']['home']['id'],
                            away_team_id=match_data['teams']['away']['id'],
                            match_status_id=status_id,
                            date=match_data['fixture']['date'],
                            stadium=match_data['fixture']['venue']['name'] if 'venue' in match_data['fixture'] and match_data['fixture']['venue'] else None,
                            referee=match_data['fixture']['referee'],
                            score_home=match_data['goals']['home'],
                            score_away=match_data['goals']['away']
                        )
                        self.db.add(new_match)
                    
                    matches_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing match data: {str(e)}")
                    continue
                    
            # Commit changes
            self.db.commit()
            
            logger.info(f"Synced {matches_count} live matches")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing live matches: {str(e)}")
            self.db.rollback()
            return False

    def _sync_single_team(self, team_id):
        """Sync a single team by ID"""
        logger.info(f"Syncing team with ID: {team_id}")
        
        # Get country mapping
        country_map = {}
        countries = self.db.query(Country).all()
        for country in countries:
            country_map[country.country_name] = country.id
        
        # Fetch team data
        response = self.football_api.get_team_info(team_id)
        
        if response and 'response' in response and response['response']:
            team_data = response['response'][0]
            
            country_name = team_data['team'].get('country')
            country_id = country_map.get(country_name)
            
            team = Team(
                id=team_data['team']['id'],
                name=team_data['team']['name'],
                logo_url=team_data['team'].get('logo'),
                country_id=country_id,
                founded=team_data['team'].get('founded'),
                venue_name=team_data.get('venue', {}).get('name'),
                venue_capacity=team_data.get('venue', {}).get('capacity'),
                # You might need to set a default league ID here
                league=None
            )
            
            existing = self.db.query(Team).filter(Team.id == team.id).first()
            if existing:
                for key, value in team.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
            else:
                self.db.add(team)
            
            self.db.commit()
            logger.info(f"Team {team_id} synced successfully")
            return True
        
        logger.error(f"No data found for team {team_id}")
        return False

    def get_status_id(self, status_short):
        """Get status ID from short name"""
        status = self.db.query(MatchStatus).filter(MatchStatus.status == status_short).first()
        return status.id if status else None
    
    async def sync_all(self):
        """Sync all data in correct order"""
        try:
            logger.info("Starting full data sync...")
            
            # 1. First sync positions (most basic static data)
            logger.info("Syncing positions...")
            self.sync_positions()
            
            # Verify positions were created
            positions = self.db.query(Position).all()
            if not positions:
                logger.error("Positions were not created! Creating them now...")
                positions_data = [
                    {"id": 1, "positions": "Goalkeeper"},
                    {"id": 2, "positions": "Defender"},
                    {"id": 3, "positions": "Midfielder"},
                    {"id": 4, "positions": "Attacker"}
                ]
                for pos_data in positions_data:
                    position = Position(**pos_data)
                    self.db.add(position)
                self.db.commit()
                logger.info("Positions created successfully")
            
            # 2. Sync event types and match statuses
            logger.info("Syncing event types...")
            self.sync_event_types()
            
            logger.info("Syncing match statuses...")
            self.sync_match_statuses()
            
            # 3. Then sync other static data
            logger.info("Syncing countries...")
            self.sync_countries()
            
            logger.info("Syncing leagues...")
            self.sync_leagues()
            
            logger.info("Syncing teams...")
            self.sync_teams()
            
            # 4. Finally sync players and matches
            logger.info("Syncing players...")
            self.sync_players()
            
            logger.info("Syncing matches...")
            self.sync_matches()
            
            logger.info("All data synced successfully")
        except Exception as e:
            logger.error(f"Error during sync_all: {e}")
            self.db.rollback()
            raise

    def sync_daily_matches(self):
        """Sync today's matches"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            matches_data = self.football_api.get_matches(date=today)
            
            if not matches_data or 'response' not in matches_data:
                logger.warning(f"No matches found for {today}")
                return
            
            matches = matches_data['response']
            logger.info(f"Found {len(matches)} matches for {today}")
            
            # Get or create the "Scheduled" match status
            scheduled_status = self.db.query(MatchStatus).filter(
                MatchStatus.status == "SCHEDULED"
            ).first()
            
            if not scheduled_status:
                scheduled_status = MatchStatus(status="SCHEDULED")
                self.db.add(scheduled_status)
                self.db.flush()
            
            for match in matches:
                try:
                    fixture = match['fixture']
                    teams = match['teams']
                    goals = match['goals']
                    league = match['league']
                    
                    # Check if match already exists
                    existing_match = self.db.query(Match).filter(
                        Match.id == fixture['id']
                    ).first()
                    
                    # Map API status to our status
                    status_map = {
                        "NS": "SCHEDULED",
                        "1H": "LIVE",
                        "HT": "LIVE",
                        "2H": "LIVE",
                        "FT": "FINISHED",
                        "AET": "FINISHED",
                        "PEN": "FINISHED",
                        "PST": "POSTPONED",
                        "CANC": "CANCELLED",
                        "ABD": "ABANDONED",
                        "AWD": "AWARDED",
                        "WO": "WALKOVER",
                        "LIVE": "LIVE"
                    }
                    
                    api_status = fixture['status']['short']
                    db_status = status_map.get(api_status, "SCHEDULED")
                    
                    # Get or create the match status
                    match_status = self.db.query(MatchStatus).filter(
                        MatchStatus.status == db_status
                    ).first()
                    
                    if not match_status:
                        match_status = MatchStatus(status=db_status)
                        self.db.add(match_status)
                        self.db.flush()
                    
                    if existing_match:
                        # Update existing match
                        existing_match.match_status_id = match_status.id
                        existing_match.score_home = goals['home'] if goals['home'] is not None else 0
                        existing_match.score_away = goals['away'] if goals['away'] is not None else 0
                    else:
                        # Get or create teams
                        home_team = self.get_or_create_team(teams['home']['id'])
                        away_team = self.get_or_create_team(teams['away']['id'])
                        
                        # Create new match
                        new_match = Match(
                            id=fixture['id'],
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            date=datetime.fromisoformat(fixture['date'].replace('Z', '+00:00')),
                            match_status_id=match_status.id,
                            score_home=goals['home'] if goals['home'] is not None else 0,
                            score_away=goals['away'] if goals['away'] is not None else 0,
                            stadium=fixture['venue']['name'] if fixture['venue']['name'] else "",
                            referee=fixture['referee'] if fixture['referee'] else ""
                        )
                        self.db.add(new_match)
                    
                    self.db.commit()
                    
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error syncing match {match.get('fixture', {}).get('id')}: {str(e)}")
                    continue
                
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in sync_daily_matches: {str(e)}")
            return False

    def get_or_create_team(self, team_id):
        """Get or create a team by API ID"""
        team = self.db.query(Team).filter(Team.id == team_id).first()
        
        if not team:
            # Fetch team data from API
            team_data = self.football_api.get_team_info(team_id)
            if team_data and 'response' in team_data and team_data['response']:
                team_info = team_data['response'][0]['team']
                venue_info = team_data['response'][0]['venue']
                
                # Get or create country
                country_name = team_info.get('country', 'Unknown')
                country = self.db.query(Country).filter(Country.country_name == country_name).first()
                
                if not country:
                    country = Country(country_name=country_name)
                    self.db.add(country)
                    self.db.flush()
                
                # Create team
                team = Team(
                    id=team_id,
                    name=team_info.get('name', ''),
                    code=team_info.get('code', ''),
                    logo_url=team_info.get('logo', ''),
                    founded=team_info.get('founded', 0),
                    venue_name=venue_info.get('name', ''),
                    venue_capacity=venue_info.get('capacity', 0),
                    country_id=country.id,
                    stadium_name=venue_info.get('name', ''),
                    team_manager='',  # We'll need to fetch this separately
                    last_updated=datetime.utcnow()
                )
                self.db.add(team)
                self.db.flush()
            else:
                # Create a minimal team record if API data not available
                team = Team(
                    id=team_id,
                    name=f"Team {team_id}",
                    logo_url="",
                    founded=0,
                    venue_name="",
                    venue_capacity=0,
                    stadium_name="",
                    team_manager="",
                    last_updated=datetime.utcnow()
                )
                self.db.add(team)
                self.db.flush()
        
        return team

    def sync_upcoming_matches(self):
        """Sync upcoming matches for today"""
        try:
            today = self.football_api.get_current_date()
            logger.info(f"Syncing upcoming matches for {today}")
            
            matches_data = self.football_api.get_matches(today)
            
            if not matches_data or 'response' not in matches_data:
                logger.error("No match data returned from API")
                return "No match data returned"
            
            matches_count = 0
            for match in matches_data['response']:
                # Only process matches that haven't started yet
                status = match['fixture']['status']['short']
                if status not in ['NS', 'TBD', 'PST', 'CANC', 'SUSP']:
                    continue
                    
                # Check if match already exists
                existing_match = self.db.query(Match).filter(Match.api_id == match['fixture']['id']).first()
                
                if existing_match:
                    # Update existing match
                    existing_match.status = status
                    existing_match.home_score = match['goals']['home'] if match['goals']['home'] is not None else 0
                    existing_match.away_score = match['goals']['away'] if match['goals']['away'] is not None else 0
                    existing_match.last_updated = datetime.now()
                else:
                    # Create new match
                    new_match = Match(
                        api_id=match['fixture']['id'],
                        league_id=match['league']['id'],
                        home_team_id=match['teams']['home']['id'],
                        away_team_id=match['teams']['away']['id'],
                        home_score=match['goals']['home'] if match['goals']['home'] is not None else 0,
                        away_score=match['goals']['away'] if match['goals']['away'] is not None else 0,
                        status=status,
                        match_date=datetime.fromisoformat(match['fixture']['date'].replace('Z', '+00:00')),
                        last_updated=datetime.now()
                    )
                    self.db.add(new_match)
                    matches_count += 1
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Synced {matches_count} upcoming matches for {today}")
            return f"Synced {matches_count} upcoming matches"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in sync_upcoming_matches: {str(e)}")
            raise

    def sync_completed_matches(self):
        """Sync completed matches with full details including events and statistics"""
        try:
            today = self.football_api.get_current_date()
            logger.info(f"Syncing completed matches for {today}")
            
            # Get all matches for today
            matches_data = self.football_api.get_matches(today)
            
            if not matches_data or 'response' not in matches_data:
                logger.error("No match data returned from API")
                return "No match data returned"
            
            updated_count = 0
            for match in matches_data['response']:
                # Only process matches that are completed
                status = match['fixture']['status']['short']
                if status not in ['FT', 'AET', 'PEN', 'ABD', 'AWD', 'WO']:
                    continue
                    
                match_id = match['fixture']['id']
                
                # Check if match already exists
                existing_match = self.db.query(Match).filter(Match.api_id == match_id).first()
                
                if existing_match:
                    # Update existing match with complete data
                    existing_match.status = status
                    existing_match.home_score = match['goals']['home'] if match['goals']['home'] is not None else 0
                    existing_match.away_score = match['goals']['away'] if match['goals']['away'] is not None else 0
                    existing_match.last_updated = datetime.now()
                    
                    # Get detailed match data including events and statistics
                    detailed_data = self.football_api.get_match_details(match_id)
                    
                    if detailed_data and 'response' in detailed_data and detailed_data['response']:
                        match_data = detailed_data['response'][0]
                        
                        # Process match events
                        if 'events' in match_data:
                            self._process_match_events(existing_match.id, match_data['events'])
                        
                        # Process match statistics
                        if 'statistics' in match_data:
                            self._process_match_statistics(existing_match.id, match_data['statistics'])
                        
                        # Process player statistics
                        if 'players' in match_data:
                            self._process_player_match_statistics(existing_match.id, match_data['players'])
                    
                    updated_count += 1
                else:
                    logger.warning(f"Match {match_id} not found in database, skipping")
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Updated {updated_count} completed matches for {today}")
            return f"Updated {updated_count} completed matches"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in sync_completed_matches: {str(e)}")
            raise
            
    def _process_match_events(self, match_id, events_data):
        """Process and store match events"""
        if not events_data:
            return
            
        try:
            # Clear existing events for this match
            self.db.query(MatchEvent).filter(MatchEvent.match_id == match_id).delete()
            
            for event in events_data:
                if 'events' not in event:
                    continue
                    
                for event_data in event['events']:
                    try:
                        # Map event type to your event_types table
                        event_type = event_data.get('type')
                        event_detail = event_data.get('detail')
                        
                        # Convert elapsed time (integer) to Time object
                        elapsed_minutes = event_data['time']['elapsed']
                        time_obj = datetime.strptime(f"{elapsed_minutes}:00", "%M:%S").time()
                        
                        # Create new event
                        new_event = MatchEvent(
                            match_id=match_id,
                            event_type_id=self._get_event_type_id(event_type),
                            minute=time_obj,  # Changed from time to minute
                            player_id=event_data['player']['id'] if 'player' in event_data and event_data['player'] else None,
                            description=event_detail  # Changed from detail to description
                        )
                        self.db.add(new_event)
                    except Exception as e:
                        logger.error(f"Error processing individual event: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"Error in _process_match_events: {str(e)}")
            raise

    def _process_match_statistics(self, match_id, statistics_data):
        """Process and store match statistics"""
        try:
            # Clear existing statistics for this match
            self.db.query(MatchStatistic).filter(MatchStatistic.match_id == match_id).delete()
            
            for team_stats in statistics_data:
                team_id = team_stats['team']['id']
                stats = team_stats['statistics']
                
                new_stats = MatchStatistic(
                    match_id=match_id,
                    team_id=team_id,
                    possession=next((int(stat['value'].replace('%', '')) for stat in stats if stat['type'] == 'Ball Possession'), None),
                    shots=next((int(stat['value']) for stat in stats if stat['type'] == 'Total Shots'), None),
                    corners=next((int(stat['value']) for stat in stats if stat['type'] == 'Corner Kicks'), None),
                    fouls=next((int(stat['value']) for stat in stats if stat['type'] == 'Fouls'), None)
                )
                self.db.add(new_stats)
                
        except Exception as e:
            logger.error(f"Error processing match statistics: {str(e)}")
            raise

    def _process_player_match_statistics(self, match_id, players_data):
        """Process and store player match statistics"""
        try:
            # Clear existing player statistics for this match
            self.db.query(PlayerMatchStatistic).filter(
                PlayerMatchStatistic.match_id == match_id
            ).delete()
            
            for team_data in players_data:
                team_id = team_data['team']['id']
                for player_data in team_data['players']:
                    stats = player_data['statistics'][0]  # Usually contains one item
                    
                    new_stats = PlayerMatchStatistic(
                        match_id=match_id,
                        player_id=player_data['player']['id'],
                        team_id=team_id,
                        minutes_played=stats.get('minutes', 0),
                        goals=stats.get('goals', {}).get('total', 0),
                        assists=stats.get('goals', {}).get('assists', 0),
                        shots=stats.get('shots', {}).get('total', 0),
                        passes=stats.get('passes', {}).get('total', 0)
                    )
                    self.db.add(new_stats)
                    
        except Exception as e:
            logger.error(f"Error processing player match statistics: {str(e)}")
            raise

    def _get_event_type_id(self, event_type):
        """Get event type ID from name"""
        event = self.db.query(EventType).filter(EventType.event == event_type).first()
        if event:
            return event.id
        # Default to a generic event type if not found
        return 1  # Assuming 1 is a valid default event type ID

class DataFetchStrategy:
    def __init__(self):
        self.REFRESH_INTERVALS = {
            'static': timedelta(days=7),    # Team info, logos, etc.
            'daily': timedelta(days=1),     # Standings, completed matches
            'frequent': timedelta(hours=4),  # Team statistics
            'live': timedelta(minutes=5)     # Live matches, scores
        }