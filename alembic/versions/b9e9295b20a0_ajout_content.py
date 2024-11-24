"""ajout content

Revision ID: b9e9295b20a0
Revises: 7a15c477b055
Create Date: 2024-03-11 16:15:02.309408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9e9295b20a0'
down_revision: Union[str, None] = '7a15c477b055'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('content', sa.String(), nullable=False))
    pass


def downgrade() -> None:
    op.drop_column("posts" , "content")
    pass
