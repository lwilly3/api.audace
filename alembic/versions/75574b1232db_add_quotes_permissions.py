"""add_quotes_permissions

Revision ID: 75574b1232db
Revises: 9eea8fc12e70
Create Date: 2026-01-07 17:52:28.740642

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75574b1232db'
down_revision: Union[str, None] = '9eea8fc12e70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout des 8 nouvelles permissions pour le module Citations
    op.add_column('user_permissions', sa.Column('quotes_view', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('quotes_create', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('quotes_edit', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('quotes_delete', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('quotes_publish', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('stream_transcription_view', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('stream_transcription_create', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('user_permissions', sa.Column('quotes_capture_live', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Suppression des colonnes en cas de rollback
    op.drop_column('user_permissions', 'quotes_capture_live')
    op.drop_column('user_permissions', 'stream_transcription_create')
    op.drop_column('user_permissions', 'stream_transcription_view')
    op.drop_column('user_permissions', 'quotes_publish')
    op.drop_column('user_permissions', 'quotes_delete')
    op.drop_column('user_permissions', 'quotes_edit')
    op.drop_column('user_permissions', 'quotes_create')
    op.drop_column('user_permissions', 'quotes_view')
