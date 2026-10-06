from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.bookmark import Bookmark
from app.models.tour_content import Event
from app.models.user import User
from app.errors import BusinessException, ErrorCode


def add_bookmark(user_id, event_id):
    if db.session.get(User, user_id) is None:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)
    if db.session.get(Event, event_id) is None:
        raise BusinessException(ErrorCode.EVENT_NOT_FOUND)

    existing = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
    if existing is not None:
        return existing, False

    bookmark = Bookmark(user_id=user_id, event_id=event_id)
    db.session.add(bookmark)
    try:
        db.session.commit()
        return bookmark, True
    except IntegrityError:
        # 동시 요청으로 동일 북마크가 먼저 저장된 경우에도 중복 생성 대신 기존 행을 반환한다.
        db.session.rollback()
        existing = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
        if existing is not None:
            return existing, False
        raise


def get_my_bookmarks(user_id):
    rows = (
        db.session.query(Bookmark, Event)
        .join(Event, Bookmark.event_id == Event.id)
        .filter(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    events = [
        {
            "id": event.id,
            "title": event.title,
            "imageUrl": event.thumbnail_url or event.image_url,
            "startDate": event.start_date,
            "endDate": event.end_date,
            "priceType": "FREE" if event.is_free else "PAID",
        }
        for _, event in rows
    ]
    return {"totalCount": len(events), "events": events}


def remove_bookmark(user_id, event_id):
    bookmark = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
    if bookmark is not None:
        db.session.delete(bookmark)
        db.session.commit()
    return {"eventId": event_id, "isBookmarked": False}
