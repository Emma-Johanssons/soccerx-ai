"""add live commentary table

Revision ID: xxxx
Revises: previous_revision_id
Create Date: 2024-xx-xx

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = 'previous_revision_id'  # replace with your last migration id
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
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_live_commentary_id'), 'live_commentary', ['id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_live_commentary_id'), table_name='live_commentary')
    op.drop_table('live_commentary') 