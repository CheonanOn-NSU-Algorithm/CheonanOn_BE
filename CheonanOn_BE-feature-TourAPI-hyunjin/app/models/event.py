# 제공받은 전국 행사 ERD의 테이블을 SQLAlchemy 모델로 정의한다.

from datetime import datetime, timezone

from app.extensions import db


def utc_now():
    # DB의 DATETIME에는 시간대 정보가 없으므로 UTC 시각을 naive datetime으로 저장한다.
    return datetime.now(timezone.utc).replace(tzinfo=None)


# MySQL에서는 BIGINT, 테스트용 SQLite에서는 자동 증가 가능한 INTEGER.
BIGINT_PK = db.BigInteger().with_variant(db.Integer(), "sqlite")


class Category(db.Model):
    # API의 세부 행사 분류를 서비스에서 사용하는 다섯 가지 분류로 묶는 기준 테이블이다.
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (db.UniqueConstraint("name", name="uq_categories_name"),)


class Sido(db.Model):
    # 지역 코드 앞 두 자리를 행사 지역과 연결한다.
    __tablename__ = "sidos"

    code = db.Column(db.CHAR(2), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)


class Event(db.Model):
    # 축제 목록·상세 응답을 한 행에 모은다. tour_content_id는 외부 API의 고유 ID다.
    __tablename__ = "events"

    id = db.Column(BIGINT_PK, primary_key=True, autoincrement=True)
    tour_content_id = db.Column(db.String(20), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    sido_code = db.Column(db.CHAR(2), db.ForeignKey("sidos.code"), nullable=False)
    lcls_code = db.Column(db.String(10))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    play_time = db.Column(db.String(500))
    venue_name = db.Column(db.String(300))
    address = db.Column(db.String(300))
    address_detail = db.Column(db.String(300))
    latitude = db.Column(db.Numeric(10, 7))
    longitude = db.Column(db.Numeric(10, 7))
    image_url = db.Column(db.String(500))
    thumbnail_url = db.Column(db.String(500))
    fee_text = db.Column(db.String(500))
    price = db.Column(db.Integer)
    is_free = db.Column(db.Boolean)
    organizer = db.Column(db.String(300))
    contact_phone = db.Column(db.String(300))
    homepage_url = db.Column(db.String(1000))
    is_permanent = db.Column(db.Boolean, nullable=False, default=False)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    tour_modified_at = db.Column(db.DateTime)
    # created_at과 updated_at은 우리 DB의 기록 시각이며, API 수정 시각과는 별개다.
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    category = db.relationship("Category")
    sido = db.relationship("Sido")
    __table_args__ = (
        db.UniqueConstraint("tour_content_id", name="uq_events_tour_content_id"),
        db.Index("idx_events_category", "category_id"),
        db.Index("idx_events_sido", "sido_code"),
        db.Index("idx_events_dates", "start_date", "end_date"),
    )


class Tag(db.Model):
    # 태그와 행사 연결은 별도 기능이다. 축제 API 적재만으로 태그를 만들지 않는다.
    __tablename__ = "tags"

    id = db.Column(BIGINT_PK, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    __table_args__ = (db.UniqueConstraint("name", name="uq_tags_name"),)


class EventTag(db.Model):
    # 행사와 태그의 다대다 연결. 두 ID를 묶어 같은 연결이 중복되지 않게 한다.
    __tablename__ = "event_tags"

    event_id = db.Column(db.BigInteger, db.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    tag_id = db.Column(db.BigInteger, db.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    __table_args__ = (db.Index("idx_event_tags_tag", "tag_id"),)


class EventDailyView(db.Model):
    # 날짜별 조회수를 저장한다. events.view_count는 행사 전체 조회수다.
    __tablename__ = "event_daily_views"

    event_id = db.Column(db.BigInteger, db.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    view_date = db.Column(db.Date, primary_key=True)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    __table_args__ = (db.Index("idx_event_daily_views_date", "view_date"),)


class Review(db.Model):
    # 한 회원은 같은 행사에 리뷰를 한 번만 작성할 수 있다.
    __tablename__ = "reviews"

    id = db.Column(BIGINT_PK, primary_key=True, autoincrement=True)
    event_id = db.Column(db.BigInteger, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.SmallInteger, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)
    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="uq_reviews_event_user"),
        db.CheckConstraint("rating BETWEEN 1 AND 5", name="chk_reviews_rating"),
        db.Index("idx_reviews_user", "user_id"),
    )


class ReviewImage(db.Model):
    # 리뷰 이미지의 sort_order는 리뷰 안에서 표시 순서를 나타낸다.
    __tablename__ = "review_images"

    id = db.Column(BIGINT_PK, primary_key=True, autoincrement=True)
    review_id = db.Column(db.BigInteger, db.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    sort_order = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    __table_args__ = (
        db.UniqueConstraint("review_id", "sort_order", name="uq_review_images_order"),
        db.CheckConstraint("sort_order BETWEEN 0 AND 4", name="chk_review_images_order"),
    )


class Bookmark(db.Model):
    # 회원과 행사를 복합 기본키로 묶어 중복 북마크를 막는다.
    __tablename__ = "bookmarks"

    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    event_id = db.Column(db.BigInteger, db.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    __table_args__ = (db.Index("idx_bookmarks_event", "event_id"),)
