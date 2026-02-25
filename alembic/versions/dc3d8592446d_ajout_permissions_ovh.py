"""ajout permissions ovh pour consultation API

Revision ID: dc3d8592446d
Revises: a5751a21438c
Create Date: 2026-02-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc3d8592446d'
down_revision: Union[str, None] = 'a5751a21438c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user_permissions', sa.Column('ovh_access_section', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_permissions', sa.Column('ovh_view_services', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_permissions', sa.Column('ovh_view_dashboard', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_permissions', sa.Column('ovh_view_billing', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_permissions', sa.Column('ovh_view_account', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('user_permissions', sa.Column('ovh_manage', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('user_permissions', 'ovh_manage')
    op.drop_column('user_permissions', 'ovh_view_account')
    op.drop_column('user_permissions', 'ovh_view_billing')
    op.drop_column('user_permissions', 'ovh_view_dashboard')
    op.drop_column('user_permissions', 'ovh_view_services')
    op.drop_column('user_permissions', 'ovh_access_section')
