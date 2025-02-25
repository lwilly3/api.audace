"""Add created_by on show and index

Revision ID: 728d86904477
Revises: 75e8b3bb0750
Create Date: 2025-02-25 18:14:34.567474

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '728d86904477'
down_revision: Union[str, None] = '75e8b3bb0750'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shows', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_index('ix_created_by_status_broadcast_date', 'shows', ['created_by', 'status', 'broadcast_date'], unique=False)
    op.create_index('ix_created_by_status_type', 'shows', ['created_by', 'status', 'type'], unique=False)
    op.create_index(op.f('ix_shows_created_by'), 'shows', ['created_by'], unique=False)
    op.create_foreign_key(None, 'shows', 'users', ['created_by'], ['id'], ondelete='SET NULL')
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=False)
    op.drop_index('ix_users_username', table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_users_username', table_name='users')
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.drop_index('ix_users_email', table_name='users')
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.drop_constraint(None, 'shows', type_='foreignkey')
    op.drop_index(op.f('ix_shows_created_by'), table_name='shows')
    op.drop_index('ix_created_by_status_type', table_name='shows')
    op.drop_index('ix_created_by_status_broadcast_date', table_name='shows')
    op.drop_column('shows', 'created_by')
    # ### end Alembic commands ###
