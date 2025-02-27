"""add season to league

Revision ID: xxx
Revises: previous_revision
Create Date: 2025-02-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('leagues', sa.Column('season', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('leagues', 'season') 