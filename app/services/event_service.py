# 저장된 행사를 화면에 제공하는 조회 서비스. 외부 TourAPI 수집과 분리한다.
# 라우트가 SQL 조건과 페이지 계산을 몰라도 되도록 목록·상세 조회를 맡는다.

from sqlalchemy import func, or_, select
from sqlalchemy.orm import joinedload

from app.errors import BusinessException, ErrorCode
from app.extensions import db
from app.models.tour_content import Event, Tag


class EventService:
    @staticmethod
    def list_events(query):
        # 요청에 있는 필터만 SQL 조건에 추가한다. 태그 검색은 EXISTS를 사용해
        # 태그가 여러 개 맞아도 한 행사가 중복되거나 totalCount가 부풀지 않게 한다.
        conditions = []
        if query["category_id"] is not None:
            conditions.append(Event.category_id == query["category_id"])
        if query["sido_code"] is not None:
            conditions.append(Event.sido_code == query["sido_code"])
        if query["is_free"] is not None:
            conditions.append(Event.is_free == query["is_free"])
        if query["start_date"] is not None:
            conditions.append(Event.end_date >= query["start_date"])
        if query["end_date"] is not None:
            conditions.append(Event.start_date <= query["end_date"])

        search_text = (query["q"] or "").strip()
        if search_text:
            # SQL LIKE의 와일드카드 입력은 일반 글자로 검색되도록 이스케이프한다.
            escaped = (
                search_text.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            keyword = f"%{escaped}%"
            conditions.append(
                or_(
                    Event.title.ilike(keyword, escape="\\"),
                    Event.venue_name.ilike(keyword, escape="\\"),
                    Event.tags.any(Tag.name.ilike(keyword, escape="\\")),
                )
            )

        # 페이지네이션 전 전체 건수를 세어 프론트가 페이지 수를 계산하게 한다.
        total_count = db.session.scalar(
            select(func.count(Event.id)).where(*conditions)
        )
        if query["sort"] == "popular":
            # 현재는 events의 누적 조회수를 기준으로 정렬한다.
            order_by = (Event.view_count.desc(), Event.id.desc())
        elif query["sort"] == "dateAsc":
            order_by = (Event.start_date.asc(), Event.id.asc())
        else:
            order_by = (Event.created_at.desc(), Event.id.desc())

        page = query["page"]
        size = query["size"]
        statement = (
            select(Event)
            .options(joinedload(Event.category), joinedload(Event.sido))
            .where(*conditions)
            .order_by(*order_by)
            .offset((page - 1) * size)
            .limit(size)
        )
        events = db.session.scalars(statement).all()
        return {
            "total_count": total_count,
            "page": page,
            "size": size,
            "events": events,
        }

    @staticmethod
    def get_event(event_id):
        # 카테고리와 지역 표시 이름을 응답에 함께 담기 위해 관계를 미리 읽는다.
        statement = (
            select(Event)
            .options(joinedload(Event.category), joinedload(Event.sido))
            .where(Event.id == event_id)
        )
        event = db.session.scalar(statement)
        if event is None:
            raise BusinessException(ErrorCode.EVENT_NOT_FOUND)
        return event
