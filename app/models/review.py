from app.extensions import db
from app.models.user import TimestampMixin

class Review(TimestampMixin, db.Model):
    __tablename__ = "review"

    # 리뷰 고유 ID
    id = db.Column(db.Integer, primary_key=True)

    # 리뷰 작성자 → User.id
    user_id = db.Column( db.Integer, nullable=False, index=True, )

    # 리뷰 대상 → TourContent.id ondelete="CASCADE", TourContent 삭제 시 관련 리뷰도 삭제
    tour_content_id = db.Column( db.Integer, nullable=False, index=True, )

    # 별점 (1~5)
    rating = db.Column( db.SmallInteger, nullable=False, )

    # 리뷰 내용
    content = db.Column( db.Text, nullable=False, )

    # DB에서 별점이 1~5 범위를 벗어나지 않도록 제한
    __table_args__ = (
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_review_rating",
        ),
    )