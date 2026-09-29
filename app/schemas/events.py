# 행사 API의 입력 검증과 화면 응답 필드를 정의한다.
# DB 조회 조건이나 값 계산은 서비스에서 처리하고 이 파일은 타입·형식만 다룬다.

from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class EventListQuerySchema(Schema):
    # 검색어는 선택값이다. 공백 제거와 검색 조건 조합은 서비스에서 처리한다.
    q = fields.String(load_default=None, validate=validate.Length(max=100))
    category_id = fields.Integer(
        load_default=None,
        validate=validate.Range(min=1),
    )
    # TourAPI 시도 코드는 두 자리 숫자 문자열이며 앞자리 0을 유지한다.
    sido_code = fields.String(
        load_default=None,
        validate=validate.Regexp(r"^[0-9]{2}$"),
    )
    is_free = fields.Boolean(load_default=None)
    # 해당 기간과 하루라도 겹치는 행사를 조회한다. 한쪽만 전달해도 된다.
    start_date = fields.Date(load_default=None)
    end_date = fields.Date(load_default=None)
    sort = fields.String(
        load_default="latest",
        validate=validate.OneOf(("latest", "popular", "dateAsc")),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))
    size = fields.Integer(load_default=20, validate=validate.Range(min=1, max=100))

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
    # 목록 카드에 필요한 값만 내보낸다. 모델의 내부 FK 대신 표시 이름을 쓴다.
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
