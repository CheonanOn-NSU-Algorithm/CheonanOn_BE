from datetime import datetime, timezone

from app.extensions import db


class Bookmark(db.Model):
    """사용자가 저장한 행사 북마크."""

    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    event = db.relationship("Event")

    # 한 사용자가 같은 행사를 중복 저장하지 못하게 한다.
    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_bookmarks_user_event"),
    )
