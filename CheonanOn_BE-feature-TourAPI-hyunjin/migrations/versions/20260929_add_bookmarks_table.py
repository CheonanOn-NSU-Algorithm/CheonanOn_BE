"""add bookmarks table

Revision ID: b7a1c9d4e2f3
Revises: f16c7e35a2b4
Create Date: 2026-09-29
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7a1c9d4e2f3"
down_revision = "f16c7e35a2b4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bookmarks",
        sa.Column(
            "user_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "event_id",
        ),
    )

    op.create_index(
        "idx_bookmarks_event",
        "bookmarks",
        ["event_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "idx_bookmarks_event",
        table_name="bookmarks",
    )

    op.drop_table("bookmarks")