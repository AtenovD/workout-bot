"""clear broken exercise media urls"""

from alembic import op


revision = "0010_clear_broken_exercise_media"
down_revision = "0009_app_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE exercises
        SET gif_url = NULL
        WHERE lower(coalesce(gif_url, '')) LIKE '%raw.githubusercontent.com/yuhonas/free-exercise-db/%'
        """
    )
    op.execute(
        """
        UPDATE exercises
        SET photo_url = NULL
        WHERE lower(coalesce(photo_url, '')) LIKE '%raw.githubusercontent.com/yuhonas/free-exercise-db/%'
        """
    )
    op.execute(
        """
        UPDATE exercises
        SET video_url = NULL
        WHERE lower(coalesce(video_url, '')) LIKE '%raw.githubusercontent.com/yuhonas/free-exercise-db/%'
        """
    )


def downgrade() -> None:
    pass
