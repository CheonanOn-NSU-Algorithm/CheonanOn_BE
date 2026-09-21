"""TourAPI에서 받은 데이터를 DB에 저장하는 코드.

Flask 앱 컨텍스트 안에서 사용하고, 저장할 때마다 별도 세션을 열어서 처리.
API 수정 시각은 한국 시간 기준으로 읽음. 다른 시간대면 api_timezone으로 지정.
"""
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import BusinessException, ErrorCode
from app.extensions import db
from app.models import TourContent, PlaceDetail, FestivalDetail
from app.models.tour_content import utc_now
from app.services.tour_api import TourAPI, CHUNGNAM_REGION_CODE, iter_pages, with_district

# 왼쪽은 API 필드명, 오른쪽은 DB 컬럼명
COMMON = {
    "title": "title",
    "addr1": "addr1",
    "addr2": "addr2",
    "zipcode": "zipcode",
    "tel": "tel",
    "homepage": "homepage",
    "overview": "overview",
    "firstimage": "first_image",
    "firstimage2": "first_image2",
    "district": "district",
}
# 관광지와 문화시설은 필드명이 달라서 따로 매핑
PLACE = {
    12: {
        "infocenter": "info_center",
        "opendate": "open_date",
        "restdate": "rest_date",
        "usetime": "use_time",
        "parking": "parking",
        "expguide": "experience_guide",
        "expagerange": "experience_age",
        "chkbabycarriage": "baby_carriage",
        "chkpet": "pet",
        "chkcreditcard": "credit_card",
    },
    14: {
        "infocenterculture": "info_center",
        "restdateculture": "rest_date",
        "usetimeculture": "use_time",
        "usefee": "use_fee",
        "parkingculture": "parking",
        "chkbabycarriageculture": "baby_carriage",
        "chkpetculture": "pet",
        "chkcreditcardculture": "credit_card",
    },
}
# 축제 정보 매핑
FESTIVAL = {
    "eventplace": "event_place",
    "playtime": "play_time",
    "usetimefestival": "use_fee",
    "sponsor1": "sponsor",
    "sponsor1tel": "sponsor_tel",
    "sponsor2": "organizer",
    "sponsor2tel": "organizer_tel",
    "program": "program",
}


def clean(value):
    # 빈 값이나 공백만 있으면 NULL로 저장
    return (
        None
        if value is None or (isinstance(value, str) and not value.strip())
        else value
    )


def date_value(value):
    # YYYYMMDD 문자열을 날짜로 바꾸기
    text = str(value)
    if not re.fullmatch(r"[0-9]{8}", text):
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_DATE)
    try:
        return datetime.strptime(text, "%Y%m%d").date()
    except ValueError as error:
        raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_DATE) from error


def assign_fields(model, item, mapping):
    # 응답에 없는 필드는 건드리지 않기. 기존 상세 정보가 지워지면 안 됨
    for source, target in mapping.items():
        if source not in item:
            continue
        value = clean(item[source])
        column = model.__table__.columns[target]
        if value is None and not column.nullable:
            raise BusinessException(
                ErrorCode.TOUR_SYNC_REQUIRED_FIELD,
                extra={"field": source},
            )
        if value is not None:
            if not isinstance(value, (str, int, float)):
                raise BusinessException(
                    ErrorCode.TOUR_SYNC_INVALID_FIELD,
                    extra={"field": source},
                )
            value = str(value)
            limit = getattr(column.type, "length", None)
            if limit and len(value) > limit:
                raise BusinessException(
                    ErrorCode.TOUR_SYNC_FIELD_TOO_LONG,
                    extra={"field": source, "limit": limit},
                )
        setattr(model, target, value)


class TourSyncService:
    # API에서 받은 목록과 상세 정보를 DB에 저장

    def __init__(self, api=None, engine=None, api_timezone=None):
        self._api = api
        self.engine = engine if engine is not None else db.engine
        self.api_timezone = api_timezone or timezone(timedelta(hours=9))

    @property
    def api(self):
        if self._api is None:
            self._api = TourAPI()
        return self._api

    def _transaction(self, operation):
        # 저장 성공하면 commit, 중간에 에러 나면 이번 저장은 rollback
        try:
            with Session(self.engine) as session, session.begin():
                return operation(session)
        except IntegrityError as error:
            raise BusinessException(ErrorCode.TOUR_SYNC_DB_CONFLICT) from error

    def _common(self, row, item):
        # 공통 정보와 좌표, 수정 시각을 DB 형식에 맞게 변환
        item = with_district(item)
        assign_fields(row, item, COMMON)
        for source, target, bound in (("mapx", "map_x", 180), ("mapy", "map_y", 90)):
            if source in item:
                value = clean(item[source])
                if value is not None:
                    try:
                        value = Decimal(str(value))
                    except InvalidOperation as error:
                        raise BusinessException(
                            ErrorCode.TOUR_SYNC_INVALID_COORDINATE,
                            extra={"field": source},
                        ) from error
                    if not value.is_finite() or abs(value) > bound:
                        raise BusinessException(
                            ErrorCode.TOUR_SYNC_COORDINATE_RANGE,
                            extra={"field": source},
                        )
                setattr(row, target, value)
        if "modifiedtime" in item:
            value = clean(item["modifiedtime"])
            if value is not None:
                if not re.fullmatch(r"[0-9]{14}", str(value)):
                    raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_MODIFIED_TIME)
                try:
                    value = datetime.strptime(str(value), "%Y%m%d%H%M%S")
                except ValueError as error:
                    raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_MODIFIED_TIME) from error
                # UTC로 바꿔서 저장. MySQL DATETIME에는 시간대 정보가 안 들어감
                value = (
                    value.replace(tzinfo=self.api_timezone)
                    .astimezone(timezone.utc)
                    .replace(tzinfo=None)
                )
            row.api_modified_at = value

    @staticmethod
    def _dates(detail, item):
        # 새로 받은 날짜만 바꾸고, 시작일과 종료일이 맞는지 확인
        for source, target in (
            ("eventstartdate", "event_start_date"),
            ("eventenddate", "event_end_date"),
        ):
            if source in item:
                setattr(detail, target, date_value(item[source]))
        if detail.event_start_date is None or detail.event_end_date is None:
            raise BusinessException(ErrorCode.TOUR_SYNC_DATES_REQUIRED)
        if detail.event_start_date > detail.event_end_date:
            raise BusinessException(ErrorCode.TOUR_SYNC_DATE_RANGE)

    @staticmethod
    def _identity(item, content_id=None, content_type=None):
        # 요청한 콘텐츠가 맞는지 ID와 타입 확인
        if not isinstance(item, dict):
            raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_ITEM)
        identifier = str(item.get("contentid", "")).strip()
        if not identifier or len(identifier) > 30:
            raise BusinessException(ErrorCode.TOUR_SYNC_INVALID_ID)
        raw_type = str(item.get("contenttypeid", ""))
        if raw_type not in {"12", "14", "15"}:
            raise BusinessException(ErrorCode.TOUR_INVALID_CONTENT_TYPE)
        kind = int(raw_type)
        if content_id is not None and identifier != content_id:
            raise BusinessException(ErrorCode.TOUR_SYNC_ID_MISMATCH)
        if content_type is not None and kind != content_type:
            raise BusinessException(ErrorCode.TOUR_SYNC_TYPE_MISMATCH)
        return identifier, kind

    def save_list_item(self, item):
        # 이미 있는 콘텐츠면 수정, 없으면 새로 저장
        identifier, kind = self._identity(item)

        def save(session):
            # 저장하는 동안 다른 요청이 같은 행을 수정하지 못하게 잠금
            row = session.scalar(
                select(TourContent)
                .where(TourContent.content_id == identifier)
                .with_for_update()
            )
            if row is None:
                row = TourContent(content_id=identifier, content_type_id=kind)
                session.add(row)
            elif row.content_type_id != kind:
                raise BusinessException(ErrorCode.TOUR_SYNC_TYPE_MISMATCH)
            if (
                (kind == 15 and row.place_detail)
                or (kind != 15 and row.festival_detail)
            ):
                raise BusinessException(ErrorCode.TOUR_SYNC_DETAIL_MISMATCH)
            self._common(row, item)
            if not row.title:
                raise BusinessException(
                    ErrorCode.TOUR_SYNC_REQUIRED_FIELD,
                    extra={"field": "title"},
                )
            if kind == 15:
                detail = row.festival_detail or FestivalDetail()
                self._dates(detail, item)
                row.festival_detail = detail
            row.last_synced_at = utc_now()
            session.flush()
            return row.id

        return self._transaction(save)

    def _pages(self, endpoint, params):
        try:
            yield from iter_pages(self.api, endpoint, params)
        except ValueError as error:
            raise BusinessException(
                ErrorCode.TOUR_API_INVALID_RESPONSE, extra={"endpoint": endpoint}
            ) from error

    @staticmethod
    def _failure(report, scope, error):
        # 메시지는 codes.py에서 가져오고, 필드명 같은 추가 정보는 따로 남김
        report["failures"].append({
            **scope,
            "code": error.error_code.code,
            "reason": error.message,
            "extra": error.extra,
        })

    def sync_list(self, content_type_id, start_date=None, end_date=None):
        # 충남 전체 목록 저장. 다시 실행해도 같은 콘텐츠는 중복으로 안 쌓임
        if content_type_id not in (12, 14, 15):
            raise BusinessException(ErrorCode.TOUR_INVALID_CONTENT_TYPE)
        params = {"lDongRegnCd": CHUNGNAM_REGION_CODE, "arrange": "A"}
        endpoint = "areaBasedList2"
        if content_type_id == 15:
            start_date, end_date = self.api.validate_festival_dates(start_date, end_date)
            params.update(eventStartDate=start_date, eventEndDate=end_date)
            endpoint = "searchFestival2"
        else:
            params["contentTypeId"] = content_type_id
        report = {"saved": 0, "failures": [], "complete": False}
        page = 0
        scope = {
            "region_code": CHUNGNAM_REGION_CODE,
            "content_type_id": content_type_id,
            "start_date": start_date,
            "end_date": end_date,
        }
        try:
            for page, items in self._pages(endpoint, params):
                for item in items:
                    try:
                        self._identity(item, content_type=content_type_id)
                        self.save_list_item(item)
                        report["saved"] += 1
                    except BusinessException as error:
                        self._failure(
                            report,
                            {**scope, "page": page, "content_id": item.get("contentid")},
                            error,
                        )
        except BusinessException as error:
            self._failure(report, {**scope, "after_page": page}, error)
        report["complete"] = not report["failures"]
        return report

    def sync_detail(self, content_id):
        # 상세 API 3개를 다 받은 뒤 한 번에 저장. 겹치는 값은 상세 정보로 갱신
        identifier = str(content_id)
        with Session(self.engine) as session:
            row = session.scalar(
                select(TourContent).where(TourContent.content_id == identifier)
            )
            if row is None:
                raise BusinessException(ErrorCode.TOUR_SYNC_CONTENT_NOT_FOUND)
            kind = row.content_type_id
        # API부터 전부 조회. 중간에 실패하면 기존 DB는 건드리지 않음
        payloads = {}
        for endpoint in ("detailCommon2", "detailIntro2", "detailInfo2"):
            params = {"contentId": identifier}
            if endpoint != "detailCommon2":
                params["contentTypeId"] = kind
            payloads[endpoint] = [
                item
                for _, items in self._pages(endpoint, params)
                for item in items
            ]
        for endpoint in ("detailCommon2", "detailIntro2"):
            if len(payloads[endpoint]) != 1:
                raise BusinessException(
                    ErrorCode.TOUR_SYNC_INVALID_DETAIL,
                    extra={"endpoint": endpoint},
                )
            item = payloads[endpoint][0]
            self._identity(
                {**item, "contenttypeid": item.get("contenttypeid", kind)},
                identifier,
                kind,
            )
        for item in payloads["detailInfo2"]:
            if "contentid" in item and str(item["contentid"]) != identifier:
                raise BusinessException(ErrorCode.TOUR_SYNC_ID_MISMATCH)

        def save(session):
            # 저장하는 동안 다른 요청이 같은 행을 수정하지 못하게 잠금
            row = session.scalar(
                select(TourContent)
                .where(TourContent.content_id == identifier)
                .with_for_update()
            )
            if row is None or row.content_type_id != kind:
                raise BusinessException(ErrorCode.TOUR_SYNC_CONTENT_CHANGED)
            if (
                (kind == 15 and row.place_detail)
                or (kind != 15 and row.festival_detail)
            ):
                raise BusinessException(ErrorCode.TOUR_SYNC_DETAIL_MISMATCH)
            self._common(row, payloads["detailCommon2"][0])
            intro = payloads["detailIntro2"][0]
            if kind == 15:
                detail = row.festival_detail or FestivalDetail()
                self._dates(detail, intro)
                assign_fields(detail, intro, FESTIVAL)
                row.festival_detail = detail
            else:
                detail = row.place_detail or PlaceDetail()
                assign_fields(detail, intro, PLACE[kind])
                row.place_detail = detail
            # 남은 정보도 나중에 쓸 수 있게 API별로 저장
            detail.detail_data = {
                **(detail.detail_data or {}),
                "detailIntro2": intro,
                "detailInfo2": payloads["detailInfo2"],
            }
            row.common_detail_synced_at = detail.last_synced_at = utc_now()
            session.flush()
            return row.id

        return self._transaction(save)

    def sync_details(self):
        # 저장된 콘텐츠를 하나씩 돌면서 상세 정보 가져오기
        with Session(self.engine) as session:
            identifiers = list(session.scalars(
                select(TourContent.content_id).order_by(TourContent.id)
            ))
        report = {
            "selected": len(identifiers),
            "saved": 0,
            "failures": [],
            "complete": False,
        }
        for identifier in identifiers:
            try:
                self.sync_detail(identifier)
                report["saved"] += 1
            except BusinessException as error:
                self._failure(report, {"content_id": identifier}, error)
        report["complete"] = not report["failures"]
        return report
