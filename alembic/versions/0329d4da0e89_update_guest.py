"""update guest

Revision ID: 0329d4da0e89
Revises: e6c6ae9227bc
Create Date: 2024-12-22 21:14:02.220655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic. modifie
revision: str = '0329d4da0e89'
down_revision: Union[str, None] = 'e6c6ae9227bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('guests', sa.Column('email', sa.String(), nullable=True))
    op.add_column('guests', sa.Column('phone', sa.String(), nullable=True))
    op.add_column('guests', sa.Column('role', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('guests', 'role')
    op.drop_column('guests', 'phone')
    op.drop_column('guests', 'email')
    # ### end Alembic commands ###
