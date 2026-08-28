"""add AI coach review fields"""

from alembic import op
import sqlalchemy as sa


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workout_reviews", sa.Column("ai_adjustment", sa.JSON()))
    op.add_column("workout_reviews", sa.Column("ai_coach_note", sa.String(512)))
    op.add_column("workout_reviews", sa.Column("ai_model", sa.String(64)))
    op.add_column("workout_reviews", sa.Column("ai_error", sa.String(256)))


def downgrade() -> None:
    op.drop_column("workout_reviews", "ai_error")
    op.drop_column("workout_reviews", "ai_model")
    op.drop_column("workout_reviews", "ai_coach_note")
    op.drop_column("workout_reviews", "ai_adjustment")
