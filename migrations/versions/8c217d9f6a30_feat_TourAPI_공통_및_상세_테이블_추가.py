"""feat: TourAPI 공통 및 상세 테이블 추가

Revision ID: 8c217d9f6a30
Revises: 3e08a9570f0c
"""
from alembic import op
import sqlalchemy as sa

revision = "8c217d9f6a30"
down_revision = "3e08a9570f0c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tour_content",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.String(30), nullable=False),
        sa.Column("content_type_id", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("addr1", sa.String(255), nullable=True),
        sa.Column("addr2", sa.String(255), nullable=True),
        sa.Column("zipcode", sa.String(20), nullable=True),
        sa.Column("tel", sa.String(100), nullable=True),
        sa.Column("homepage", sa.Text(), nullable=True),
        sa.Column("overview", sa.Text(), nullable=True),
        sa.Column("first_image", sa.String(500), nullable=True),
        sa.Column("first_image2", sa.String(500), nullable=True),
        sa.Column("map_x", sa.Numeric(13, 10), nullable=True),
        sa.Column("map_y", sa.Numeric(12, 10), nullable=True),
        sa.Column("district", sa.String(20), nullable=True),
        sa.Column("api_modified_at", sa.DateTime(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=False),
        sa.Column("common_detail_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("content_type_id IN (12, 14, 15)", name="ck_tour_content_type"),
    )
    op.create_index("ix_tour_content_content_id", "tour_content", ["content_id"], unique=True)
    op.create_index("ix_tour_content_content_type_id", "tour_content", ["content_type_id"], unique=False)
    op.create_index("ix_tour_content_district", "tour_content", ["district"], unique=False)
    op.create_table(
        "place_detail",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_content_id", sa.Integer(), sa.ForeignKey("tour_content.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("info_center", sa.String(100), nullable=True),
        sa.Column("open_date", sa.String(100), nullable=True),
        sa.Column("rest_date", sa.String(255), nullable=True),
        sa.Column("use_time", sa.Text(), nullable=True),
        sa.Column("use_fee", sa.Text(), nullable=True),
        sa.Column("parking", sa.Text(), nullable=True),
        sa.Column("experience_guide", sa.Text(), nullable=True),
        sa.Column("experience_age", sa.String(255), nullable=True),
        sa.Column("baby_carriage", sa.String(100), nullable=True),
        sa.Column("pet", sa.String(100), nullable=True),
        sa.Column("credit_card", sa.String(100), nullable=True),
        sa.Column("detail_data", sa.JSON(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "festival_detail",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_content_id", sa.Integer(), sa.ForeignKey("tour_content.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("event_start_date", sa.Date(), nullable=False),
        sa.Column("event_end_date", sa.Date(), nullable=False),
        sa.Column("event_place", sa.String(255), nullable=True),
        sa.Column("play_time", sa.Text(), nullable=True),
        sa.Column("use_fee", sa.Text(), nullable=True),
        sa.Column("sponsor", sa.String(255), nullable=True),
        sa.Column("sponsor_tel", sa.String(100), nullable=True),
        sa.Column("organizer", sa.String(255), nullable=True),
        sa.Column("organizer_tel", sa.String(100), nullable=True),
        sa.Column("program", sa.Text(), nullable=True),
        sa.Column("detail_data", sa.JSON(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("event_start_date <= event_end_date", name="ck_festival_date_range"),
    )
    op.create_index("ix_festival_detail_event_start_date", "festival_detail", ["event_start_date"], unique=False)
    op.create_index("ix_festival_detail_event_end_date", "festival_detail", ["event_end_date"], unique=False)


def downgrade():
    op.drop_table("festival_detail")
    op.drop_table("place_detail")
    op.drop_table("tour_content")

