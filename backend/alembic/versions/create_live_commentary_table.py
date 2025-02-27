"""create live commentary table

Revision ID: create_live_commentary
Revises: # leave empty if this is your first migration
Create Date: 2024-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic
revision = 'create_live_commentary'
down_revision = None  # replace with your last migration ID if you have one
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'live_commentary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('match_id', sa.Integer(), nullable=True),
        sa.Column('minute', sa.Integer(), nullable=True),
        sa.Column('commentary', sa.String(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), 
                 server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_live_commentary_id'), 'live_commentary', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_live_commentary_id'), table_name='live_commentary')
    op.drop_table('live_commentary') 