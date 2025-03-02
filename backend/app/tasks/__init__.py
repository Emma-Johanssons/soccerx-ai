import logging

logger = logging.getLogger(__name__)

# Import all functions from the original tasks.py
from app.tasks.tasks import (
    fetch_team_statistics,
    sync_static_data,
    sync_daily_data,
    sync_live_matches,
    sync_daily_matches,
    sync_team_data,
    sync_all_data,
    sync_todays_matches,
    sync_statistics
)

# Import from test_task.py
from app.tasks.test_task import test_redis_connection

# Make all these functions available when importing from app.tasks
__all__ = [
    'fetch_team_statistics',
    'test_redis_connection',
    'sync_static_data',
    'sync_daily_data',
    'sync_live_matches',
    'sync_daily_matches',
    'sync_team_data',
    'sync_all_data',
    'sync_todays_matches',
    'sync_statistics'
]