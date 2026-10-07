from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.bookmark import Bookmark
from app.models.tour_content import Event
from app.models.user import User
from app.errors import BusinessException, ErrorCode


def add_bookmark(user_id, event_id):
    """북마크를 생성하고 (모델, 새로 생성했는지)를 반환한다.

    이미 저장된 항목은 중복 행 없이 성공으로 처리한다. 대상 회원이나 행사가 없으면
    공통 오류 응답으로 바뀔 업무 예외를 던진다.
    """
    # FK 오류 대신 누락된 대상이 회원인지 행사인지 먼저 구분한다.
    if db.session.get(User, user_id) is None:
        raise BusinessException(ErrorCode.USER_NOT_FOUND)
    if db.session.get(Event, event_id) is None:
        raise BusinessException(ErrorCode.EVENT_NOT_FOUND)

    existing = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
    if existing is not None:
        return existing, False

    # 고유 제약 조건은 동시에 들어온 요청에서도 중복 저장을 막는 최종 방어선이다.
    bookmark = Bookmark(user_id=user_id, event_id=event_id)
    db.session.add(bookmark)
    try:
        db.session.commit()
        return bookmark, True
    except IntegrityError:
        # 다른 요청이 먼저 저장했을 수 있어 세션을 되돌린 뒤 기존 행을 다시 조회한다.
        db.session.rollback()
        existing = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
        if existing is not None:
            return existing, False
        raise


def get_my_bookmarks(user_id):
    """사용자의 북마크를 최근 저장 순으로 조회해 API 응답 형식으로 변환한다."""
    # 행사 제목·날짜도 필요하므로 북마크와 행사 테이블을 조인해 한 번에 읽는다.
    rows = (
        db.session.query(Bookmark, Event)
        .join(Event, Bookmark.event_id == Event.id)
        .filter(Bookmark.user_id == user_id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    # ORM 모델을 클라이언트 응답용 camelCase 필드가 담긴 dict로 바꾼다.
    events = [
        {
            "id": event.id,
            "title": event.title,
            "imageUrl": event.thumbnail_url or event.image_url,
            "startDate": event.start_date,
            "endDate": event.end_date,
            # 내부 Boolean 대신 API에서 정한 문자열 값으로 가격 유형을 노출한다.
            "priceType": "FREE" if event.is_free else "PAID",
        }
        for _, event in rows
    ]
    return {"totalCount": len(events), "events": events}


def remove_bookmark(user_id, event_id):
    """북마크를 지운다. 이미 없어도 해제된 상태로 같은 응답을 반환한다."""
    bookmark = Bookmark.query.filter_by(user_id=user_id, event_id=event_id).first()
    if bookmark is not None:
        db.session.delete(bookmark)
        db.session.commit()
    return {"eventId": event_id, "isBookmarked": False}
