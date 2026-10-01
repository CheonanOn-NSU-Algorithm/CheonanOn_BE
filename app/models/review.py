# 리뷰(review) 모델과 공통 시간 필드를 정의한다.
#
# Review는 사용자가 특정 행사(TourContent)에 작성한 리뷰를 저장한다.
# 리뷰 생성 및 수정 시각은 TimestampMixin을 통해 자동으로 관리한다.

from datetime import datetime, timezone

from app.extensions import db


class TimestampMixin:
    """모델의 생성 및 수정 시각을 공통으로 관리하는 Mixin."""

    # 레코드가 생성될 때 현재 UTC 시각을 자동으로 저장한다.
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # 레코드 생성 시 현재 UTC 시각을 저장한다.
    # 이후 해당 레코드가 수정되면 현재 UTC 시각으로 자동 갱신된다.
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class Review(TimestampMixin, db.Model):
    """행사에 작성된 리뷰 정보를 저장하는 모델."""

    __tablename__ = "review"

    # 리뷰의 고유 ID
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # 리뷰를 작성한 사용자 ID
    user_id = db.Column(
        db.Integer,
        nullable=False,
        index=True,
    )

    # 리뷰가 작성된 행사 ID
    tour_content_id = db.Column(
        db.Integer,
        nullable=False,
        index=True,
    )

    # 리뷰 별점
    rating = db.Column(
        db.SmallInteger,
        nullable=False,
    )

    # 리뷰 내용
    content = db.Column(
        db.Text,
        nullable=False,
    )

    # DB에서도 별점이 1점에서 5점 사이인지 검증한다.
    __table_args__ = (
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_review_rating",
        ),
    )