"""merge social_page_insights and current head

Revision ID: cd42bf43298f
Revises: 4d507a930cc2, b7c2e9f4a1d3
Create Date: 2026-03-02 20:08:11.253119

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd42bf43298f'
down_revision: Union[str, None] = ('4d507a930cc2', 'b7c2e9f4a1d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
