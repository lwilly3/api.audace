"""add social articles permissions to user_permissions

Revision ID: 7f3a92b1c4d8
Revises: 48c872301416
Create Date: 2026-03-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3a92b1c4d8'
down_revision: Union[str, None] = '48c872301416'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_permissions', sa.Column('social_view_articles', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_create_articles', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_edit_articles', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_delete_articles', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('user_permissions', 'social_delete_articles')
    op.drop_column('user_permissions', 'social_edit_articles')
    op.drop_column('user_permissions', 'social_create_articles')
    op.drop_column('user_permissions', 'social_view_articles')
