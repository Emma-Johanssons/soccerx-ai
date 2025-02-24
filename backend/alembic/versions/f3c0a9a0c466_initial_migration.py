"""Initial migration

Revision ID: f3c0a9a0c466
Revises: 
Create Date: 2025-02-20 17:25:53.715683

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3c0a9a0c466'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Drop all tables with CASCADE to handle dependencies
    op.execute("""
        DROP TABLE IF EXISTS player_match_statistics CASCADE;
        DROP TABLE IF EXISTS match_events CASCADE;
        DROP TABLE IF EXISTS player_matches CASCADE;
        DROP TABLE IF EXISTS team_statistics CASCADE;
        DROP TABLE IF EXISTS match_statistics CASCADE;
        DROP TABLE IF EXISTS matches CASCADE;
        DROP TABLE IF EXISTS players CASCADE;
        DROP TABLE IF EXISTS teams CASCADE;
        DROP TABLE IF EXISTS leagues CASCADE;
        DROP TABLE IF EXISTS positions CASCADE;
        DROP TABLE IF EXISTS countries CASCADE;
        DROP TABLE IF EXISTS match_statuses CASCADE;
        DROP TABLE IF EXISTS event_types CASCADE;
        DROP TABLE IF EXISTS last_sync CASCADE;
    """)

def downgrade():
    # Tables will be recreated by SQLAlchemy
    pass
