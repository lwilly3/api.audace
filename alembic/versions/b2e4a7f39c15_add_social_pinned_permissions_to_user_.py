"""add social pinned permissions to user_permissions

Revision ID: b2e4a7f39c15
Revises: 7f3a92b1c4d8
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e4a7f39c15'
down_revision: Union[str, None] = '7f3a92b1c4d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_permissions', sa.Column('social_view_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_create_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_edit_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('user_permissions', sa.Column('social_delete_pinned', sa.Boolean(), server_default=sa.text('false'), nullable=False))


def downgrade() -> None:
    op.drop_column('user_permissions', 'social_delete_pinned')
    op.drop_column('user_permissions', 'social_edit_pinned')
    op.drop_column('user_permissions', 'social_create_pinned')
    op.drop_column('user_permissions', 'social_view_pinned')
