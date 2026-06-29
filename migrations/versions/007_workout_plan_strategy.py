"""add workout plan strategy fields"""

from alembic import op
import sqlalchemy as sa


revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workout_plans", sa.Column("cycle_length_weeks", sa.Integer(), nullable=False, server_default="6"))
    op.add_column("workout_plans", sa.Column("current_week", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("workout_plans", sa.Column("current_session_index", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("workout_plans", sa.Column("strategy", sa.JSON(), nullable=True))
    op.add_column("workout_plans", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))


def downgrade() -> None:
    op.drop_column("workout_plans", "updated_at")
    op.drop_column("workout_plans", "strategy")
    op.drop_column("workout_plans", "current_session_index")
    op.drop_column("workout_plans", "current_week")
    op.drop_column("workout_plans", "cycle_length_weeks")

