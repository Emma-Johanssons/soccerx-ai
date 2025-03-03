"""add form column to team statistics

Revision ID: 02eae0565bfa
Revises: 01eae0565bf3
Create Date: 2024-04-03 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision: str = '02eae0565bfa'
down_revision: Union[str, None] = '01eae0565bf3'  # This should be your last successful migration ID
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add form column if it doesn't exist
    op.add_column('team_statistics', sa.Column('form', JSON, nullable=True))

def downgrade() -> None:
    op.drop_column('team_statistics', 'form')