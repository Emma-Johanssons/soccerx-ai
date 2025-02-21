"""update_league_model

Revision ID: [some_hash]
Revises: [previous_hash]
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Drop all tables with CASCADE to handle dependencies
    op.execute("""
        DROP SCHEMA public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO postgres;
        GRANT ALL ON SCHEMA public TO public;
    """)

def downgrade():
    pass 