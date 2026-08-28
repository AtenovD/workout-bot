"""add gif_url to exercises

Revision ID: 0002_gif_url
Revises: 0001_initial
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_gif_url"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("gif_url", sa.String(512), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "gif_url")
