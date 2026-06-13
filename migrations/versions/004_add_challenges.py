"""add user_challenges table"""
revision = '004'
down_revision = '003_fix_reminders_add_referrals'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'user_challenges',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('challenge_code', sa.String(32), nullable=False, server_default='30day'),
        sa.Column('started_at', sa.Date(), nullable=False),
        sa.Column('current_day', sa.Integer(), server_default='0'),
        sa.Column('completed_days', sa.Integer(), server_default='0'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_completed', sa.Boolean(), server_default='false'),
    )
    op.create_index('ix_user_challenges_user_id', 'user_challenges', ['user_id'])


def downgrade():
    op.drop_index('ix_user_challenges_user_id', 'user_challenges')
    op.drop_table('user_challenges')
