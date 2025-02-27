"""add last sync table

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'last_sync',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(), nullable=False),
        sa.Column('last_synced', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sync_type')
    )

def downgrade():
    op.drop_table('last_sync') 