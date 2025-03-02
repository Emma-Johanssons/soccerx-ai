"""add assist player to match events

Revision ID: xxx
Revises: previous_revision
Create Date: 2024-02-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('match_events', sa.Column('assist_player_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_match_events_assist_player',
        'match_events', 'players',
        ['assist_player_id'], ['id']
    )

def downgrade():
    op.drop_constraint('fk_match_events_assist_player', 'match_events', type_='foreignkey')
    op.drop_column('match_events', 'assist_player_id') 