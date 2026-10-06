from marshmallow import Schema, ValidationError, fields, validates_schema


class BookmarkCreateSchema(Schema):
    # camelCase matches the team's earlier bookmark API; event_id stays accepted for existing clients.
    eventId = fields.Integer(required=False)
    event_id = fields.Integer(required=False)

    @validates_schema
    def validate_event_id(self, data, **kwargs):
        if ("eventId" in data) == ("event_id" in data):
            raise ValidationError({"eventId": ["eventId 값을 하나만 입력해주세요."]})


class BookmarkResponseSchema(Schema):
    eventId = fields.Integer(required=True)
    isBookmarked = fields.Boolean(required=True)


class BookmarkEventSchema(Schema):
    id = fields.Integer(required=True)
    title = fields.String(required=True)
    imageUrl = fields.String(allow_none=True)
    startDate = fields.Date(required=True)
    endDate = fields.Date(required=True)
    priceType = fields.String(required=True)


class BookmarkListResponseSchema(Schema):
    totalCount = fields.Integer(required=True)
    events = fields.List(fields.Nested(BookmarkEventSchema), required=True)
