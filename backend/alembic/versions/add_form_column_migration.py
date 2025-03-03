"""add form column to team statistics

Revision ID: 02eae0565bfa
Revises: 01eae0565bf3
Create Date: 2024-03-03 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers
revision = '02eae0565bfa'
down_revision = '01eae0565bf3'  # Make sure this matches your last successful migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('team_statistics', sa.Column('form', JSON, nullable=True))

def downgrade() -> None:
    op.drop_column('team_statistics', 'form') 