"""add match status and event types

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-02-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create match_statuses table
    op.create_table(
        'match_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create event_types table
    op.create_table(
        'event_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

def downgrade():
    op.drop_table('event_types')
    op.drop_table('match_statuses') 