"""update positions table

Revision ID: xxxx
Revises: previous_revision_id
Create Date: 2025-02-24 23:22:06.652

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Drop existing table if it exists
    op.drop_table('positions', if_exists=True)
    
    # Create new positions table
    op.create_table('positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Insert default positions
    op.execute("""
        INSERT INTO positions (id, name, code) VALUES 
        (1, 'Goalkeeper', 'GK'),
        (2, 'Defender', 'DEF'),
        (3, 'Midfielder', 'MID'),
        (4, 'Attacker', 'ATT')
    """)

def downgrade():
    op.drop_table('positions') 