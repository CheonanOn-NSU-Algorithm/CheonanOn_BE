from marshmallow import Schema, fields, post_dump


class ErrorResponseSchema(Schema):
    """공통 오류 응답의 필수 필드를 직렬화한다.

    오류별 부가 정보(errors, reason 등)는 기존 API 계약을 유지하도록
    최상위 필드로 그대로 전달한다.
    """

    success = fields.Boolean(required=True)
    code = fields.String(required=True)
    message = fields.String(required=True)

    @post_dump(pass_original=True)
    def preserve_extra_fields(self, serialized, original, **kwargs):
        """오류 코드별 확장 필드를 보존해 기존 클라이언트 응답을 유지한다."""
        serialized.update(
            {key: value for key, value in original.items() if key not in serialized}
        )
        return serialized
