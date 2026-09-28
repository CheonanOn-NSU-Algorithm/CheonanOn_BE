"""제공받은 전국 행사 ERD와 초기 카테고리·시도 데이터.

Revision ID: c2b0d920b672
Revises: 8c217d9f6a30
"""

from alembic import op
import sqlalchemy as sa

revision = "c2b0d920b672"
down_revision = "8c217d9f6a30"
branch_labels = None
depends_on = None

BIGINT_PK = sa.BigInteger().with_variant(sa.Integer(), "sqlite")
MYSQL = {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}


def upgrade():
    # 이 리비전은 새 ERD 테이블을 생성한다. 같은 이름의 테이블이 있으면 덮어쓰지 않는다.
    target_tables = {"users", "categories", "sidos", "events", "tags", "event_tags",
                     "event_daily_views", "reviews", "review_images", "bookmarks"}
    existing = target_tables.intersection(sa.inspect(op.get_bind()).get_table_names())
    if existing:
        raise RuntimeError(f"기존 테이블과 충돌합니다. 마이그레이션 전에 DB 이력을 확인하세요: {sorted(existing)}")

    # 회원, 행사, 분류와 지역을 먼저 만들고 나서 이를 참조하는 참여 테이블을 만든다.
    op.create_table("users",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("kakao_id", sa.String(64), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("profile_image_url", sa.String(500)),
        sa.Column("terms_agreed_at", sa.DateTime, nullable=False),
        sa.Column("privacy_agreed_at", sa.DateTime, nullable=False),
        sa.Column("last_login_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("kakao_id", name="uq_users_kakao_id"), **MYSQL)
    op.create_table("categories",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("name", name="uq_categories_name"), **MYSQL)
    op.create_table("sidos",
        sa.Column("code", sa.CHAR(2), primary_key=True),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("short_name", sa.String(10), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"), **MYSQL)
    op.create_table("events",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("tour_content_id", sa.String(20), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id"), nullable=False),
        sa.Column("sido_code", sa.CHAR(2), sa.ForeignKey("sidos.code"), nullable=False),
        sa.Column("lcls_code", sa.String(10)),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("play_time", sa.String(500)),
        sa.Column("venue_name", sa.String(300)),
        sa.Column("address", sa.String(300)),
        sa.Column("address_detail", sa.String(300)),
        sa.Column("latitude", sa.Numeric(10, 7)),
        sa.Column("longitude", sa.Numeric(10, 7)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("thumbnail_url", sa.String(500)),
        sa.Column("fee_text", sa.String(500)),
        sa.Column("price", sa.Integer),
        sa.Column("is_free", sa.Boolean),
        sa.Column("organizer", sa.String(300)),
        sa.Column("contact_phone", sa.String(300)),
        sa.Column("homepage_url", sa.String(1000)),
        sa.Column("is_permanent", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tour_modified_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("tour_content_id", name="uq_events_tour_content_id"), **MYSQL)
    op.create_index("idx_events_category", "events", ["category_id"])
    op.create_index("idx_events_sido", "events", ["sido_code"])
    op.create_index("idx_events_dates", "events", ["start_date", "end_date"])
    op.create_table("tags",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.UniqueConstraint("name", name="uq_tags_name"), **MYSQL)
    op.create_table("event_tags",
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.BigInteger, sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True), **MYSQL)
    op.create_index("idx_event_tags_tag", "event_tags", ["tag_id"])
    op.create_table("event_daily_views",
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("view_date", sa.Date, primary_key=True),
        sa.Column("view_count", sa.Integer, nullable=False, server_default="0"), **MYSQL)
    op.create_index("idx_event_daily_views_date", "event_daily_views", ["view_date"])
    op.create_table("reviews",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.SmallInteger, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("event_id", "user_id", name="uq_reviews_event_user"),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_reviews_rating"), **MYSQL)
    op.create_index("idx_reviews_user", "reviews", ["user_id"])
    op.create_table("review_images",
        sa.Column("id", BIGINT_PK, primary_key=True, autoincrement=True),
        sa.Column("review_id", sa.BigInteger, sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint("review_id", "sort_order", name="uq_review_images_order"),
        sa.CheckConstraint("sort_order BETWEEN 0 AND 4", name="chk_review_images_order"), **MYSQL)
    op.create_table("bookmarks",
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.BigInteger, sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()), **MYSQL)
    op.create_index("idx_bookmarks_event", "bookmarks", ["event_id"])

    # 앱에서 사용하는 기준 데이터는 마이그레이션에 포함해 빈 DB에서도 바로 적재 가능하게 한다.
    categories = sa.table("categories", sa.column("name", sa.String), sa.column("sort_order", sa.Integer))
    op.bulk_insert(categories, [{"name": name, "sort_order": order} for order, name in enumerate(
        ("축제", "전시", "공연", "체험", "계절행사"), 1)])
    sidos = sa.table("sidos", sa.column("code", sa.String), sa.column("name", sa.String),
                     sa.column("short_name", sa.String), sa.column("sort_order", sa.Integer))
    regions = (("11", "서울특별시", "서울"), ("41", "경기도", "경기"),
               ("26", "부산광역시", "부산"), ("51", "강원특별자치도", "강원"),
               ("44", "충청남도", "충남"), ("28", "인천광역시", "인천"),
               ("27", "대구광역시", "대구"), ("30", "대전광역시", "대전"),
               ("31", "울산광역시", "울산"), ("36", "세종특별자치시", "세종"),
               ("43", "충청북도", "충북"), ("52", "전북특별자치도", "전북"),
               ("12", "전남광주통합특별시", "전남광주"), ("47", "경상북도", "경북"),
               ("48", "경상남도", "경남"), ("50", "제주특별자치도", "제주"))
    op.bulk_insert(sidos, [{"code": code, "name": name, "short_name": short,
                            "sort_order": order} for order, (code, name, short) in enumerate(regions, 1)])


def downgrade():
    # 외래 키 의존성이 있는 테이블부터 역순으로 제거한다. 운영 데이터 삭제에 주의해야 한다.
    for table in ("bookmarks", "review_images", "reviews", "event_daily_views",
                  "event_tags", "tags", "events", "sidos", "categories", "users"):
        op.drop_table(table)
