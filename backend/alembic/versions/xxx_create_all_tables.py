"""create all tables

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-02-25 14:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create positions table if not exists
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create match_statuses table if not exists
    op.create_table(
        'match_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create event_types table if not exists
    op.create_table(
        'event_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('event_types')
    op.drop_table('match_statuses')
    op.drop_table('positions') 