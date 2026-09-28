from marshmallow import Schema, fields


class BookmarkCreateSchema(Schema):
    eventId = fields.Integer(required=True)


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
    events = fields.List(
        fields.Nested(BookmarkEventSchema)
    )