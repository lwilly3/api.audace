"""ajout de la table users

Revision ID: 5a19a2e5baf8
Revises: 10c62a322286
Create Date: 2024-03-08 23:17:26.860816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a19a2e5baf8'
down_revision: Union[str, None] = '10c62a322286'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 10h57
def upgrade() -> None:
    op.create_table("users",
                     sa.Column('id',sa.Integer(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('password',sa.String(),nullable=False),
                    sa.Column('created_at', sa.TIMESTAMP(timezone=True),
                              server_default=sa.text('now()'), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email')

    )
    pass


def downgrade() -> None:
    op.drop_table('users')
    pass
