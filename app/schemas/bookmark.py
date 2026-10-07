from marshmallow import Schema, ValidationError, fields, validates_schema


class BookmarkCreateSchema(Schema):
    """camelCase와 기존 snake_case 요청을 받아 북마크 추가 입력을 검증한다."""

    # 두 표기를 모두 허용해 기존 클라이언트도 계속 요청할 수 있다.
    eventId = fields.Integer(required=False)
    event_id = fields.Integer(required=False)

    @validates_schema
    def validate_event_id(self, data, **kwargs):
        """두 입력 키 중 정확히 하나만 전달됐는지 확인한다."""
        if ("eventId" in data) == ("event_id" in data):
            raise ValidationError({"eventId": ["eventId 값을 하나만 입력해주세요."]})


class BookmarkResponseSchema(Schema):
    """추가·삭제 뒤 행사 ID와 북마크 최종 상태를 반환한다."""

    eventId = fields.Integer(required=True)
    isBookmarked = fields.Boolean(required=True)


class BookmarkEventSchema(Schema):
    """내 북마크 목록 한 항목에 포함할 행사 요약 정보 형식."""

    id = fields.Integer(required=True)
    title = fields.String(required=True)
    imageUrl = fields.String(allow_none=True)
    startDate = fields.Date(required=True)
    endDate = fields.Date(required=True)
    priceType = fields.String(required=True)


class BookmarkListResponseSchema(Schema):
    """행사 요약 목록과 전체 개수를 묶은 응답 형식."""

    totalCount = fields.Integer(required=True)
    events = fields.List(fields.Nested(BookmarkEventSchema), required=True)
