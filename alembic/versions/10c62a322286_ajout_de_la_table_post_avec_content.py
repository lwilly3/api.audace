"""ajout de la table post avec content

Revision ID: 10c62a322286
Revises: 
Create Date: 2024-03-08 23:12:43.695340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10c62a322286'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('posts', sa.Column('id', sa.Integer(), nullable=False, primary_key=True))
    op.add_column('posts', sa.Column('title', sa.String(), nullable=False))

    pass

# alembic revision -m "nom de la revision"
# alembic heads
# alembic upgrade head
#10h48    alembic upgrade [version]
def downgrade() ->  None:
    op.drop_table('posts')
    pass
