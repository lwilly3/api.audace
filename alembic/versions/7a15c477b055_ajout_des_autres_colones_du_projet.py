"""ajout des autres colones du projet

Revision ID: 7a15c477b055
Revises: ce223e06d99f
Create Date: 2024-03-11 16:06:28.854442

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a15c477b055'
down_revision: Union[str, None] = 'ce223e06d99f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("posts", sa.Column(
        "published", sa.Boolean(), nullable=False, server_default="True"
    ))
    op.add_column("posts", sa.Column(
        "created_at", sa.TIMESTAMP(timezone=True), nullable= False, server_default=sa.text("now()")
    ))
    pass


def downgrade() -> None:
    op.drop_column("posts", "published")
    op.drop_column("posts", "created_at")
    pass
