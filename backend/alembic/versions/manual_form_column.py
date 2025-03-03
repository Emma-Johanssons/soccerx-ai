"""record manual form column addition

Revision ID: manual_form_add
Revises: 01eae0565bf3
Create Date: 2024-03-03 17:00:00.000000

"""
from typing import Sequence, Union

# revision identifiers
revision = 'manual_form_add'
down_revision = '01eae0565bf3'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Column was added manually via SQL
    pass

def downgrade() -> None:
    # Column was added manually via SQL
    pass 