"""003_fix_reminders_add_referrals

Revision ID: 0003_fix_reminders_add_referrals
Revises: 0002_gif_url
Create Date: 2026-06-13

Fixes:
 - reminders table: replace one-shot fields (scheduled_at, payload, is_sent)
   with recurring-reminder fields (time_of_day, days_of_week, enabled)
 - referrals table: new table for referral system
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_fix_reminders_add_referrals'
down_revision = '0002_gif_url'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── reminders: drop old one-shot columns ─────────────────────────────
    with op.batch_alter_table('reminders') as batch:
        batch.drop_column('scheduled_at')
        batch.drop_column('payload')
        batch.drop_column('is_sent')
        batch.add_column(sa.Column('time_of_day', sa.Time(), nullable=False,
                                   server_default='08:00:00'))
        batch.add_column(sa.Column('days_of_week', sa.String(32),
                                   server_default='1,2,3,4,5,6,7'))
        batch.add_column(sa.Column('enabled', sa.Boolean(),
                                   server_default='true'))

    # ── referrals ─────────────────────────────────────────────────────────
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('referrer_id', sa.BigInteger(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('referred_id', sa.BigInteger(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False, unique=True),
        sa.Column('xp_granted', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index('ix_referrals_referrer_id', 'referrals', ['referrer_id'])


def downgrade() -> None:
    op.drop_table('referrals')

    with op.batch_alter_table('reminders') as batch:
        batch.drop_column('time_of_day')
        batch.drop_column('days_of_week')
        batch.drop_column('enabled')
        batch.add_column(sa.Column('scheduled_at',
                                   sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column('payload', sa.JSON()))
        batch.add_column(sa.Column('is_sent', sa.Boolean(),
                                   server_default='false'))
