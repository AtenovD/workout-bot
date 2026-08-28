"""add workout reviews and skipped exercise flag"""

from alembic import op
import sqlalchemy as sa


revision = "0005_workout_reviews"
down_revision = "0004_add_challenges"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "session_exercises",
        sa.Column("was_skipped", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_table(
        "workout_reviews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("workout_session_id", sa.BigInteger(), sa.ForeignKey("workout_sessions.id"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("intensity_feedback", sa.String(16)),
        sa.Column("pain_feedback", sa.String(16)),
        sa.Column("skipped_exercise_ids", sa.JSON()),
        sa.Column("skipped_exercise_names", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_workout_reviews_workout_session_id", "workout_reviews", ["workout_session_id"])
    op.create_index("ix_workout_reviews_user_id", "workout_reviews", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_workout_reviews_user_id", table_name="workout_reviews")
    op.drop_index("ix_workout_reviews_workout_session_id", table_name="workout_reviews")
    op.drop_table("workout_reviews")
    op.drop_column("session_exercises", "was_skipped")
