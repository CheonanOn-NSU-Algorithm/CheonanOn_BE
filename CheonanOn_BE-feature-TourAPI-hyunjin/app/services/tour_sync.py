# 전국 축제 API 응답을 ERD의 events 테이블로 변환해 저장한다.
# 호출 시 Flask 앱 컨텍스트가 필요하며, 이 파일은 HTTP 라우트나 자동 실행을 만들지 않는다.

import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import BusinessException, ErrorCode
from app.extensions import db
from app.models import Category, Event, Sido
from app.services.tour_api import TourAPI, iter_pages


def category_name(code):
    # API의 세부 분류를 ERD에 정의된 다섯 카테고리 중 하나로 묶는다.
    code = str(code or "")
    if code == "EV010500":
        return "계절행사"
    if code.startswith("EV01"):
        return "축제"
    if code.startswith("EV02"):
        return "공연"
    if code == "EV030100":
        return "전시"
    if code.startswith(("EV0302", "EV0303", "EV0304")):
        return "체험"
    raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_FIELD, extra={"field": "lclsSystm3"})


def text_value(value, limit=None, truncate=False):
    # 공백뿐인 값은 NULL로 저장하고, 컬럼 길이를 넘는 값은 기본적으로 오류로 처리한다.
    # 요금 안내만 예외적으로 잘라 저장할 수 있게 truncate 옵션을 둔다.
    if value is None:
        return None
    if not isinstance(value, (str, int, float)):
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_FIELD)
    result = str(value).strip() or None
    if result and limit and len(result) > limit:
        if truncate:
            return result[:limit]
        raise BusinessException(ErrorCode.TOUR_SYNC_FIELD_TOO_LONG, extra={"limit": limit})
    return result


def date_value(value):
    raw = str(value or "")
    if not re.fullmatch(r"[0-9]{8}", raw):
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_DATE)
    try:
        return datetime.strptime(raw, "%Y%m%d").date()
    except ValueError as error:
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_DATE) from error


def modified_value(value):
    if not value:
        return None
    raw = str(value)
    if not re.fullmatch(r"[0-9]{14}", raw):
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_MODIFIED_TIME)
    try:
        return datetime.strptime(raw, "%Y%m%d%H%M%S")
    except ValueError as error:
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_MODIFIED_TIME) from error


def coordinate_value(value, bound, field):
    # 숫자가 아니거나 위도·경도의 물리적 범위를 벗어나면 해당 행을 적재하지 않는다.
    if value is None or str(value).strip() == "":
        return None
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_COORDINATE, extra={"field": field}) from error
    if not result.is_finite() or abs(result) > bound:
        raise BusinessException(ErrorCode.TOUR_SYNC_COORDINATE_RANGE, extra={"field": field})
    return result


def price_from_fee(fee_text):
    # 원문 요금 안내를 보존하면서 검색용 최저 가격·무료 여부를 추정한다.
    # 무료와 유료가 섞였거나 해석이 불분명하면 임의의 가격을 만들지 않는다.
    if not fee_text:
        return None, None
    compact = re.sub(r"\s+", "", fee_text)
    if compact in {"무료", "무료입장", "입장무료"}:
        return 0, True
    amounts = re.findall(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d+)\s*원", fee_text)
    if amounts and "무료" not in fee_text:
        return min(int(amount.replace(",", "")) for amount in amounts), False
    return None, None


class TourSyncService:
    def __init__(self, api=None, engine=None):
        self._api = api
        self.engine = engine if engine is not None else db.engine

    @property
    def api(self):
        if self._api is None:
            self._api = TourAPI()
        return self._api

    @staticmethod
    def _identity(item, expected=None):
        if not isinstance(item, dict):
            raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_ITEM)
        identifier = text_value(item.get("contentid"), 20)
        if not identifier:
            raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_ID)
        if str(item.get("contenttypeid", "")) != "15":
            raise BusinessException(ErrorCode.TOUR_INVALID_CONTENT_TYPE)
        if expected is not None and identifier != expected:
            raise BusinessException(ErrorCode.TOUR_SYNC_ID_MISMATCH)
        return identifier

    @staticmethod
    def _failure(report, scope, error):
        report["failures"].append({
            **scope, "code": error.error_code.code,
            "reason": error.message, "extra": error.extra,
        })

    def _transaction(self, operation):
        # 행사 한 건을 독립 트랜잭션으로 저장한다. 실패한 건만 롤백하고 나머지는 계속 처리한다.
        try:
            with Session(self.engine) as session, session.begin():
                return operation(session)
        except IntegrityError as error:
            raise BusinessException(ErrorCode.TOUR_SYNC_DB_CONFLICT) from error

    @staticmethod
    def _set_list_fields(row, item):
        # 목록 API에 있는 공통 필드를 저장한다. 상세 API 전용 필드는 여기서 지우지 않는다.
        title = text_value(item.get("title"), 200)
        if not title:
            raise BusinessException(ErrorCode.TOUR_SYNC_REQUIRED_FIELD, extra={"field": "title"})
        start = date_value(item.get("eventstartdate"))
        end = date_value(item.get("eventenddate"))
        if start > end:
            raise BusinessException(ErrorCode.TOUR_SYNC_DATE_RANGE)
        row.title, row.start_date, row.end_date = title, start, end
        row.lcls_code = text_value(item.get("lclsSystm3"), 10)
        row.is_permanent = (end - start).days > 90
        row.tour_modified_at = modified_value(item.get("modifiedtime"))
        for source, target, limit in (
            ("addr1", "address", 300), ("addr2", "address_detail", 300),
            ("firstimage", "image_url", 500), ("firstimage2", "thumbnail_url", 500),
            ("tel", "contact_phone", 300),
        ):
            if source in item:
                setattr(row, target, text_value(item[source], limit))
        if "mapy" in item:
            row.latitude = coordinate_value(item["mapy"], 90, "mapy")
        if "mapx" in item:
            row.longitude = coordinate_value(item["mapx"], 180, "mapx")

    def save_list_item(self, item):
        # TourAPI의 contentid를 고유 키로 사용해 신규 행을 만들거나 기존 행을 갱신한다.
        # 기존 행의 PK는 유지하므로 나중에 연결될 리뷰·북마크 참조도 바뀌지 않는다.
        identifier = self._identity(item)
        category = category_name(item.get("lclsSystm3"))
        raw_region = text_value(item.get("lDongRegnCd"))
        if not raw_region or not re.fullmatch(r"[0-9]{2,5}", raw_region):
            raise BusinessException(ErrorCode.TOUR_SYNC_REQUIRED_FIELD, extra={"field": "lDongRegnCd"})
        sido_code = raw_region[:2]

        def save(session):
            category_row = session.scalar(select(Category).where(Category.name == category))
            if category_row is None or session.get(Sido, sido_code) is None:
                raise BusinessException(ErrorCode.TOUR_SYNC_REQUIRED_FIELD,
                                        extra={"field": "category/sido seed", "sido_code": sido_code})
            row = session.scalar(select(Event).where(
                Event.tour_content_id == identifier).with_for_update())
            modified = modified_value(item.get("modifiedtime"))
            # API 수정 시각이 같으면 목록 필드가 그대로라고 보고 불필요한 UPDATE를 건너뛴다.
            if row is not None and modified is not None and row.tour_modified_at == modified:
                return "unchanged"
            if row is None:
                row = Event(tour_content_id=identifier)
                session.add(row)
            row.category_id = category_row.id
            row.sido_code = sido_code
            self._set_list_fields(row, item)
            session.flush()
            return "saved"

        return self._transaction(save)

    def _pages(self, endpoint, params):
        try:
            yield from iter_pages(self.api, endpoint, params)
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE, extra={"endpoint": endpoint}) from error

    def sync_list(self, content_type_id=15, start_date=None, end_date=None):
        # contentTypeId 15(축제)만 허용한다. 지역 필터 없이 searchFestival2를 순회한다.
        if content_type_id != 15:
            raise BusinessException(ErrorCode.TOUR_INVALID_CONTENT_TYPE)
        start_date, end_date = self.api.validate_festival_dates(start_date, end_date)
        report = {"saved": 0, "unchanged": 0, "failures": [], "complete": False}
        scope = {"start_date": start_date, "end_date": end_date}
        page = 0
        try:
            for page, items in self._pages("searchFestival2", {
                "eventStartDate": start_date, "eventEndDate": end_date,
            }):
                for item in items:
                    try:
                        report[self.save_list_item(item)] += 1
                    except BusinessException as error:
                        self._failure(report, {**scope, "page": page,
                                               "content_id": item.get("contentid") if isinstance(item, dict) else None}, error)
        except BusinessException as error:
            self._failure(report, {**scope, "after_page": page}, error)
        report["complete"] = not report["failures"]
        return report

    def import_json(self, path):
        # 이미 받은 searchFestival2 JSON 파일을 API 호출 없이 초기 적재할 때 사용한다.
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        items = payload["response"]["body"]["items"]["item"]
        if not isinstance(items, list):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)
        report = {"saved": 0, "unchanged": 0, "failures": [], "complete": False}
        for index, item in enumerate(items):
            try:
                report[self.save_list_item(item)] += 1
            except BusinessException as error:
                self._failure(report, {"index": index,
                                       "content_id": item.get("contentid") if isinstance(item, dict) else None}, error)
        report["complete"] = not report["failures"]
        return report

    def _detail_item(self, endpoint, identifier):
        # 상세 API는 행사 ID당 한 항목이어야 한다. 0건이나 중복은 잘못된 응답으로 처리한다.
        params = {"contentId": identifier}
        if endpoint == "detailIntro2":
            params["contentTypeId"] = 15
        items = [item for _, page in self._pages(endpoint, params) for item in page]
        if len(items) != 1:
            raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_DETAIL, extra={"endpoint": endpoint})
        # 상세 응답에 contenttypeid가 없을 수 있으므로 목록에서 확인한 타입을 사용한다.
        self._identity({**items[0], "contenttypeid": 15}, identifier)
        return items[0]

    def sync_detail(self, content_id):
        # 목록에 저장된 행사만 상세 조회한다. 두 API 응답을 모두 받은 뒤 한 번에 저장한다.
        identifier = str(content_id)
        with Session(self.engine) as session:
            if session.scalar(select(Event.id).where(Event.tour_content_id == identifier)) is None:
                raise BusinessException(ErrorCode.TOUR_SYNC_CONTENT_NOT_FOUND)
        common = self._detail_item("detailCommon2", identifier)
        intro = self._detail_item("detailIntro2", identifier)

        def save(session):
            row = session.scalar(select(Event).where(
                Event.tour_content_id == identifier).with_for_update())
            if row is None:
                raise BusinessException(ErrorCode.TOUR_SYNC_CONTENT_CHANGED)
            if "overview" in common:
                row.description = text_value(common["overview"])
            if "homepage" in common:
                row.homepage_url = text_value(common["homepage"], 1000)
            for source, target, limit in (
                ("eventplace", "venue_name", 300), ("playtime", "play_time", 500),
                ("usetimefestival", "fee_text", 500), ("sponsor1", "organizer", 300),
            ):
                if source in intro:
                    # fee_text는 설계상 500자이므로 긴 원문은 앞 500자만 저장한다.
                    setattr(row, target, text_value(intro[source], limit, truncate=target == "fee_text"))
            if row.fee_text is not None:
                row.price, row.is_free = price_from_fee(row.fee_text)
            session.flush()
            return row.id

        return self._transaction(save)

    def sync_details(self):
        # 목록 적재 후 전체 행을 순회한다. 한 건이 실패해도 나머지는 계속 진행한다.
        with Session(self.engine) as session:
            identifiers = list(session.scalars(select(Event.tour_content_id).order_by(Event.id)))
        report = {"selected": len(identifiers), "saved": 0, "failures": [], "complete": False}
        for identifier in identifiers:
            try:
                self.sync_detail(identifier)
                report["saved"] += 1
            except BusinessException as error:
                self._failure(report, {"content_id": identifier}, error)
        report["complete"] = not report["failures"]
        return report
