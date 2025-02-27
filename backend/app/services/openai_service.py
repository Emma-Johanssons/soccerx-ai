from openai import OpenAI
from ..config import settings
import logging
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.last_stats_comment_time = {}  # Track when we last made stats comments

    def generate_commentary(self, match_data: Dict[str, Any], events: List[Dict[str, Any]], 
                          statistics: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate commentary based on match events and statistics"""
        try:
            if not match_data or not match_data.get('fixture'):
                logger.warning("Invalid match data received")
                return None
            
            match_id = match_data['fixture'].get('id')
            logger.info(f"Generating commentary for match {match_id}")
            logger.info(f"Events: {events}")
            logger.info(f"Statistics: {statistics}")
            
            fixture_status = match_data.get('fixture', {}).get('status', {}).get('short')
            
            if not fixture_status or fixture_status in ['NS', 'TBD', 'SUSP', 'PST']:
                logger.info(f"Match {match_id} hasn't started yet or status is invalid")
                return None
            
            # Generate commentary for significant events
            if events:
                latest_event = events[-1]
                logger.info(f"Generating commentary for event: {latest_event}")
                commentary = self._create_event_commentary(match_data, latest_event)
                if commentary:
                    logger.info(f"Generated event commentary: {commentary}")
                    return commentary
            
            # Every 15 minutes, comment on statistics if available
            current_time = match_data.get('fixture', {}).get('status', {}).get('elapsed', 0)
            last_stats_time = self.last_stats_comment_time.get(match_id, 0)
            
            if statistics and (current_time - last_stats_time >= 15):
                logger.info(f"Generating statistics commentary for match {match_id}")
                self.last_stats_comment_time[match_id] = current_time
                commentary = self._create_stats_commentary(match_data, statistics)
                if commentary:
                    logger.info(f"Generated stats commentary: {commentary}")
                    return commentary
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating commentary: {str(e)}")
            logger.exception(e)  # Log the full stack trace
            return None

    def _create_event_commentary(self, match_data: Dict[str, Any], event: Dict[str, Any]) -> Optional[str]:
        """Create commentary for a match event"""
        try:
            logger.info(f"Creating event commentary for match {match_data['fixture']['id']}")
            logger.info(f"Event data: {event}")
            
            # Create prompt based on event type
            event_type = event.get('type', '').lower()
            if event_type in ['goal', 'card', 'subst']:
                prompt = self._create_event_prompt(match_data, event)
                logger.info(f"Generated prompt: {prompt}")
                
                # Generate commentary using OpenAI
                commentary = self._generate_text(prompt)
                logger.info(f"Generated commentary: {commentary}")
                return commentary
            
            return None
        except Exception as e:
            logger.error(f"Error creating event commentary: {str(e)}")
            return None

    def _create_stats_commentary(self, match_data: Dict[str, Any], statistics: Dict[str, Any]) -> Optional[str]:
        """Create commentary based on match statistics"""
        try:
            logger.info(f"Creating stats commentary for match {match_data['fixture']['id']}")
            logger.info(f"Statistics data: {statistics}")
            
            # Create prompt for statistics
            prompt = self._create_stats_prompt(match_data, statistics)
            logger.info(f"Generated prompt: {prompt}")
            
            # Generate commentary using OpenAI
            commentary = self._generate_text(prompt)
            logger.info(f"Generated commentary: {commentary}")
            return commentary
        except Exception as e:
            logger.error(f"Error creating stats commentary: {str(e)}")
            return None

    def _create_event_prompt(self, match_data: Dict[str, Any], event: Dict[str, Any]) -> str:
        """Create a prompt for match event commentary"""
        try:
            event_type = event.get('type', '').lower()
            player_name = event.get('player', {}).get('name', 'Unknown Player')
            team_name = event.get('team', {}).get('name', 'Unknown Team')
            minute = event.get('time', {}).get('elapsed', 0)
            
            if event_type == 'goal':
                return f"Create a brief, exciting commentary for a goal scored by {player_name} for {team_name} in the {minute}th minute."
            elif event_type == 'card':
                card_type = event.get('detail', 'card')
                return f"Create a brief commentary for a {card_type} shown to {player_name} of {team_name} in the {minute}th minute."
            elif event_type == 'subst':
                assist_name = event.get('assist', {}).get('name', 'Unknown Player')
                return f"Create a brief commentary for a substitution where {player_name} replaces {assist_name} for {team_name} in the {minute}th minute."
            
            return None
        except Exception as e:
            logger.error(f"Error creating event prompt: {str(e)}")
            return None

    def _create_stats_prompt(self, match_data: Dict[str, Any], statistics: Dict[str, Any]) -> str:
        # Implementation of _create_stats_prompt method
        pass

    def _generate_text(self, prompt: str) -> str:
        # Implementation of _generate_text method
        pass 