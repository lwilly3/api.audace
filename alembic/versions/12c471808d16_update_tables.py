"""update tables

Revision ID: 12c471808d16
Revises: 0329d4da0e89
Create Date: 2024-12-23 17:01:36.032883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12c471808d16'
down_revision: Union[str, None] = '0329d4da0e89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('emissions', sa.Column('type', sa.Text(), nullable=True))
    op.add_column('emissions', sa.Column('duration', sa.Integer(), nullable=True))
    op.add_column('emissions', sa.Column('frequency', sa.Text(), nullable=True))
    op.add_column('emissions', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('guests', sa.Column('avatar', sa.Text(), nullable=True))
    op.drop_column('presenters', 'biography')
    op.add_column('users', sa.Column('profilePicture', sa.Text(), nullable=True))
    op.drop_index('ix_users_username', table_name='users')
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    op.drop_column('users', 'profilePicture')
    op.add_column('presenters', sa.Column('biography', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column('guests', 'avatar')
    op.drop_column('emissions', 'description')
    op.drop_column('emissions', 'frequency')
    op.drop_column('emissions', 'duration')
    op.drop_column('emissions', 'type')
    # ### end Alembic commands ###