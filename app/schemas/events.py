# 행사 API의 입력 검증과 화면 응답 필드를 정의한다.
# DB 조회 조건이나 값 계산은 서비스에서 처리하고 이 파일은 타입·형식만 다룬다.

import re

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_dump,
    pre_load,
    validate,
    validates_schema,
)


class QuerySchema(Schema):
    # 같은 키가 반복되면 첫 값만 남기지 않고 요청 오류로 처리한다.
    # MultiDict를 여기서 변환하므로 라우터에는 요청값 해석 로직이 필요 없다.
    @pre_load
    def normalize_query(self, data, **kwargs):
        if hasattr(data, "getlist"):
            duplicates = {
                key: ["같은 파라미터는 한 번만 입력해주세요."]
                for key in data
                if len(data.getlist(key)) != 1
            }
            if duplicates:
                raise ValidationError(duplicates)
            return data.to_dict()
        return data


class EmptyQuerySchema(QuerySchema):
    # 선택지·상세 API는 쿼리를 받지 않는다. 알 수 없는 키는 Schema가 거부한다.
    pass


class EventPathSchema(Schema):
    # URL이 정수여도 DB의 INT PK 범위를 벗어나면 DB 접근 전에 거부한다.
    event_id = fields.Integer(
        required=True, validate=validate.Range(min=1, max=2_147_483_647)
    )


class CategoryOptionSchema(Schema):
    # 화면에 name을 표시하고 선택한 id를 목록 API의 category_id로 전달한다.
    id = fields.Integer()
    name = fields.String()
    sort_order = fields.Integer(data_key="sortOrder")


class SidoOptionSchema(Schema):
    # 칩에는 shortName, 전체 지역명에는 name을 쓴다. code는 문자열 그대로 전달한다.
    code = fields.String()
    name = fields.String()
    short_name = fields.String(data_key="shortName")
    sort_order = fields.Integer(data_key="sortOrder")


class EventListQuerySchema(QuerySchema):
    # 검색어는 선택값이다. 공백 제거와 검색 조건 조합은 서비스에서 처리한다.
    q = fields.String(load_default=None, validate=validate.Length(max=100))
    category_id = fields.Integer(
        load_default=None,
        validate=validate.Range(min=1, max=2_147_483_647),
    )
    # TourAPI 시도 코드는 두 자리 숫자 문자열이며 앞자리 0을 유지한다.
    sido_code = fields.String(
        load_default=None,
        validate=validate.Regexp(r"^[0-9]{2}$"),
    )
    is_free = fields.Boolean(load_default=None, truthy={"true"}, falsy={"false"})
    # 해당 기간과 하루라도 겹치는 행사를 조회한다. 한쪽만 전달해도 된다.
    start_date = fields.Date(load_default=None)
    end_date = fields.Date(load_default=None)
    sort = fields.String(
        load_default="latest",
        validate=validate.OneOf(("latest", "popular", "dateAsc")),
    )
    # DB에서 처리할 수 없는 초대형 OFFSET이 만들어지지 않도록 상한도 검증한다.
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, max=2_147_483_647),
    )
    size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))

    @pre_load
    def validate_date_format(self, data, **kwargs):
        # ISO 파서는 다른 날짜 표기도 받을 수 있어 API에서 약속한 모양부터 검사한다.
        errors = {}
        for key in ("start_date", "end_date"):
            if key in data and (
                not isinstance(data[key], str)
                or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", data[key])
            ):
                errors[key] = ["날짜는 YYYY-MM-DD 형식으로 입력해주세요."]
        if errors:
            raise ValidationError(errors)
        return data

    @validates_schema
    def validate_period(self, data, **kwargs):
        # 두 날짜가 모두 있으면 뒤집힌 검색 기간을 DB 조회 전에 거부한다.
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise ValidationError(
                {"end_date": ["종료일은 시작일보다 빠를 수 없습니다."]}
            )


class EventCardSchema(Schema):
    # 목록 카드의 표시 이름과 필터 재선택에 필요한 분류 ID·지역 코드를 내보낸다.
    id = fields.Integer()
    title = fields.String()
    category_id = fields.Integer(data_key="categoryId")
    category = fields.Function(lambda event: event.category.name)
    sido_code = fields.String(data_key="sidoCode")
    sido = fields.Function(lambda event: event.sido.short_name)
    start_date = fields.Date(data_key="startDate")
    end_date = fields.Date(data_key="endDate")
    venue_name = fields.String(data_key="venueName", allow_none=True)
    thumbnail_url = fields.String(data_key="thumbnailUrl", allow_none=True)
    price = fields.Integer(allow_none=True)
    is_free = fields.Boolean(data_key="isFree", allow_none=True)


class EventListResponseSchema(Schema):
    # totalCount는 현재 페이지 건수가 아니라 같은 필터의 전체 결과 건수다.
    total_count = fields.Integer(data_key="totalCount")
    page = fields.Integer()
    size = fields.Integer()
    events = fields.List(fields.Nested(EventCardSchema))


class MonthlyTopQuerySchema(QuerySchema):
    # 월을 생략하면 한국 시간 기준 현재 달을 사용한다. 카드 개수는 최대 20개다.
    month = fields.Date(format="%Y-%m", load_default=None)
    size = fields.Integer(load_default=4, validate=validate.Range(min=1, max=20))

    @pre_load
    def validate_month_format(self, data, **kwargs):
        # strptime은 2026-9도 허용하므로 파싱 전에 명세의 YYYY-MM 모양을 검사한다.
        # 존재하지 않는 월이나 0000년은 아래 Date 필드가 달력 기준으로 거부한다.
        month = data.get("month")
        if "month" in data and (
            not isinstance(month, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", month)
        ):
            raise ValidationError({"month": ["조회 월은 YYYY-MM 형식으로 입력해주세요."]})
        return data


class MonthlyTopEventSchema(Schema):
    # 서비스의 행사 객체와 월간 조회수를 카드 필드 하나로 합쳐 반환한다.
    event = fields.Nested(EventCardSchema)
    monthly_views = fields.Integer(data_key="monthlyViews")

    @post_dump
    def flatten_card(self, data, **kwargs):
        # 내부의 event 묶음을 풀어 기존 카드와 동일한 필드 옆에 monthlyViews를 둔다.
        return {**data["event"], "monthlyViews": data["monthlyViews"]}


class MonthlyTopResponseSchema(Schema):
    month = fields.String()
    events = fields.List(fields.Nested(MonthlyTopEventSchema))


class EventDetailSchema(EventCardSchema):
    # 카드 필드에 행사 소개·연락처·지도 좌표를 더해 상세 화면에 사용한다.
    description = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    address_detail = fields.String(data_key="addressDetail", allow_none=True)
    play_time = fields.String(data_key="playTime", allow_none=True)
    fee_text = fields.String(data_key="feeText", allow_none=True)
    image_url = fields.String(data_key="imageUrl", allow_none=True)
    latitude = fields.Float(allow_none=True)
    longitude = fields.Float(allow_none=True)
    organizer = fields.String(allow_none=True)
    contact_phone = fields.String(data_key="contactPhone", allow_none=True)
    homepage_url = fields.String(data_key="homepageUrl", allow_none=True)
    is_permanent = fields.Boolean(data_key="isPermanent")
