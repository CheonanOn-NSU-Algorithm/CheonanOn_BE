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
    #
    # User 테이블의 id를 참조한다.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True,
    )

    # 리뷰가 작성된 행사 ID
    #
    # Event 테이블의 id를 참조한다.
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
        index=True,
    )

    # 리뷰가 작성된 행사
    event = db.relationship("Event")

    # 리뷰 별점
    #
    # db.Numeric(2, 1)
    #   - Numeric: 소수점 자릿수를 정확하게 관리하기 위한 자료형
    #   - 2: 전체 자릿수(precision)
    #   - 1: 소수점 이하 자릿수(scale)
    #
    # Numeric(2, 1)은 전체 숫자 자릿수가 최대 2자리이고,
    # 소수점 이하 자릿수는 1자리까지 저장할 수 있다.
    #
    # 따라서 0.5 단위의 평점을 표현하기에 적합하다.
    #
    rating = db.Column(
        db.Numeric(2, 1),
        nullable=False,
    )

    # 리뷰 내용
    content = db.Column(
        db.Text,
        nullable=False,
    )

    # ============================================================
    # Review 테이블 제약 조건
    # ============================================================
    #
    # 애플리케이션의 Schema에서 이미 rating 값을 검증하지만,
    # DB에도 동일한 조건을 설정하여 잘못된 값이 저장되는 것을
    # 한 번 더 방지한다.
    #
    # DB에 직접 데이터를 넣거나,
    # 다른 코드에서 Schema 검증을 거치지 않고 데이터를 저장하더라도
    # 잘못된 평점이 DB에 저장되는 것을 방지할 수 있다.
    #
    __table_args__ = (
        db.CheckConstraint(

            # ----------------------------------------------------
            # 1. 평점의 최소값과 최대값을 검사한다.
            # ----------------------------------------------------
            #
            # rating은 0.5점보다 작을 수 없고
            # 5점을 초과할 수 없다.
            "rating >= 0.5 AND rating <= 5 "

            # ----------------------------------------------------
            # 2. 0.5점 단위인지 검사한다.
            # ----------------------------------------------------
            #
            # rating에 2를 곱했을 때 정수가 되어야 한다.
            # 정수가 되지 않는 값은 허용하지 않는다.
            #
            # FLOOR()는 숫자의 소수점 이하를 버린다.
            #   rating * 2 = FLOOR(rating * 2)
            #
            # 조건을 만족하려면 rating * 2가 정수여야 한다.
            #
            "AND rating * 2 = FLOOR(rating * 2)",

            # DB에 생성되는 Check Constraint의 이름이다.
            #
            # 이후 Migration을 확인하거나
            # Constraint를 수정/삭제할 때 이 이름을 사용한다.
            #
            name="ck_review_rating",
        ),
    )