"""add bookmarks table

Revision ID: a91c2d7e4b10
Revises: fd8da9482b62
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa


revision = "a91c2d7e4b10"
down_revision = "fd8da9482b62"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "bookmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], name="fk_bookmarks_event_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_bookmarks_user_id", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "event_id", name="uq_bookmarks_user_event"),
    )
    with op.batch_alter_table("bookmarks", schema=None) as batch_op:
        batch_op.create_index("ix_bookmarks_event_id", ["event_id"], unique=False)
        batch_op.create_index("ix_bookmarks_user_id", ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("bookmarks", schema=None) as batch_op:
        batch_op.drop_index("ix_bookmarks_user_id")
        batch_op.drop_index("ix_bookmarks_event_id")
    op.drop_table("bookmarks")
