"""add on db user permissions

Revision ID: 2aa8889d4cd1
Revises: 93c6f091bafb
Create Date: 2025-03-14 21:56:23.368075

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2aa8889d4cd1'
down_revision: Union[str, None] = '93c6f091bafb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_permissions', sa.Column('can_create_presenters', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_view_tasks', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_create_tasks', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_edit_tasks', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_delete_tasks', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_assign_tasks', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_view_archives', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_destroy_archives', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_restore_archives', sa.Boolean(), nullable=True))
    op.add_column('user_permissions', sa.Column('can_delete_archives', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_permissions', 'can_delete_archives')
    op.drop_column('user_permissions', 'can_restore_archives')
    op.drop_column('user_permissions', 'can_destroy_archives')
    op.drop_column('user_permissions', 'can_view_archives')
    op.drop_column('user_permissions', 'can_assign_tasks')
    op.drop_column('user_permissions', 'can_delete_tasks')
    op.drop_column('user_permissions', 'can_edit_tasks')
    op.drop_column('user_permissions', 'can_create_tasks')
    op.drop_column('user_permissions', 'can_view_tasks')
    op.drop_column('user_permissions', 'can_create_presenters')
    # ### end Alembic commands ###
