"""add_match_statistics_with_extend

Revision ID: 01eae0565bf3
Revises: f3c0a9a0c466
Create Date: 2025-02-24 19:08:42.917807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01eae0565bf3'
down_revision: Union[str, None] = 'f3c0a9a0c466'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
