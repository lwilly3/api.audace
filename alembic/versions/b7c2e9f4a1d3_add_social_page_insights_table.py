"""add social_page_insights table

Revision ID: b7c2e9f4a1d3
Revises: a9d4371840fb
Create Date: 2026-03-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7c2e9f4a1d3'
down_revision = 'a9d4371840fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('social_page_insights'):
        return

    op.create_table(
        'social_page_insights',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        # Impressions page
        sa.Column('page_impressions_unique', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_posts_impressions', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_posts_impressions_unique', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_posts_impressions_organic', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_posts_impressions_paid', sa.Integer(), server_default='0', nullable=False),
        # Engagement page
        sa.Column('page_post_engagements', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_views_total', sa.Integer(), server_default='0', nullable=False),
        # Followers
        sa.Column('page_follows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_daily_follows', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_daily_unfollows', sa.Integer(), server_default='0', nullable=False),
        # Reactions detaillees
        sa.Column('reactions_like', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reactions_love', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reactions_wow', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reactions_haha', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reactions_sorry', sa.Integer(), server_default='0', nullable=False),
        sa.Column('reactions_anger', sa.Integer(), server_default='0', nullable=False),
        # Video
        sa.Column('page_video_views', sa.Integer(), server_default='0', nullable=False),
        sa.Column('page_video_view_time', sa.Integer(), server_default='0', nullable=False),
        # Soft delete
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(['account_id'], ['social_accounts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('account_id', 'date', name='uq_page_insight_account_date'),
    )
    op.create_index(op.f('ix_social_page_insights_id'), 'social_page_insights', ['id'], unique=False)
    op.create_index(op.f('ix_social_page_insights_account_id'), 'social_page_insights', ['account_id'], unique=False)
    op.create_index(op.f('ix_social_page_insights_date'), 'social_page_insights', ['date'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_social_page_insights_date'), table_name='social_page_insights')
    op.drop_index(op.f('ix_social_page_insights_account_id'), table_name='social_page_insights')
    op.drop_index(op.f('ix_social_page_insights_id'), table_name='social_page_insights')
    op.drop_table('social_page_insights')
