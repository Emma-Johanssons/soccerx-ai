from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from ..database import get_db
from ..sql_models.models import LiveCommentary, Match  # Updated import
from ..api_service.football_api import FootballAPIService
from ..services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{match_id}")
def get_match_commentary(match_id: int, db: Session = Depends(get_db)):
    """Get commentary for a specific match"""
    try:
        # Get all commentary from database
        all_commentary = (
            db.query(LiveCommentary)  # Updated model
            .filter(LiveCommentary.match_id == match_id)
            .order_by(LiveCommentary.created_at.desc())
            .all()
        )
        
        return {
            "status": "success",
            "data": {
                "commentary": [
                    {
                        "id": c.id,
                        "minute": c.minute,
                        "commentary": c.commentary,
                        "event_type": c.event_type,
                        "created_at": c.created_at.isoformat()
                    } for c in all_commentary
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting commentary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{match_id}")
def create_match_commentary(match_id: int, db: Session = Depends(get_db)):
    """Generate new commentary for a match"""
    try:
        # Get match details
        football_api = FootballAPIService()
        match_data = football_api.get_match_details(match_id)
        
        if not match_data or not match_data.get('response'):
            return {"status": "success", "data": {"commentary": []}}
            
        match_details = match_data['response'][0]
        match_status = match_details['fixture']['status']['short']
        
        # Only generate commentary for live matches
        if match_status in ['1H', '2H', 'HT']:
            # Get recent events and statistics
            events = football_api.get_match_events(match_id)
            statistics = football_api.get_match_statistics(match_id)
            
            # Generate commentary
            openai_service = OpenAIService()
            commentary = openai_service.generate_commentary(
                match_details,
                events.get('response', [])[-5:],  # Last 5 events
                statistics.get('response', [{}])[0] if statistics.get('response') else None
            )
            
            if commentary:
                elapsed_time = match_details['fixture']['status']['elapsed']
                new_commentary = LiveCommentary(  # Updated model
                    match_id=match_id,
                    minute=elapsed_time,
                    commentary=commentary,
                    event_type='event' if events.get('response') else 'stats',
                )
                db.add(new_commentary)
                db.commit()
                
                return {
                    "status": "success",
                    "data": {
                        "commentary": {
                            "id": new_commentary.id,
                            "minute": new_commentary.minute,
                            "commentary": new_commentary.commentary,
                            "event_type": new_commentary.event_type,
                            "created_at": new_commentary.created_at.isoformat()
                        }
                    }
                }
        
        return {
            "status": "success",
            "data": {
                "message": "No new commentary generated"
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating commentary: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 