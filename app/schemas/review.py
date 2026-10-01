# 리뷰 API의 요청 및 응답 형식을 정의하는 marshmallow 스키마.
#
# 모델 객체를 그대로 요청/응답에 사용하지 않고 스키마를 거치는 이유:
#   요청 데이터의 형식과 필수값을 검증할 수 있다.
#   응답에 노출할 필드만 명시할 수 있다.
#   나중에 모델에 필드가 추가되어도 불필요한 데이터가 응답에 포함되는 것을 막을 수 있다.

from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class ReviewCreateSchema(Schema):
    """리뷰 생성 요청용 스키마.

    POST /reviews 요청에서 전달되는 데이터를 검증한다.
    """

    # 리뷰를 작성한 사용자 ID
    user_id = fields.Integer(required=True)

    # 리뷰를 작성할 관광 콘텐츠 ID
    tour_content_id = fields.Integer(required=True)

    # 평점은 1점부터 5점까지만 허용한다.
    rating = fields.Integer(
        required=True,
        validate=validate.Range(
            min=1,
            max=5,
            error="평점은 1점에서 5점 사이여야 합니다."
        )
    )

    # 리뷰 내용은 최소 1글자 이상 입력해야 한다.
    content = fields.String(
        required=True,
        validate=validate.Length(
            min=1,
            error="리뷰 내용을 입력해주세요."
        )
    )


class ReviewUpdateSchema(Schema):
    """리뷰 수정 요청용 스키마.

    PUT /reviews/{review_id} 요청에서 수정할 데이터를 검증한다.
    수정하지 않는 필드는 생략할 수 있다.
    """

    # 평점은 수정하지 않을 수 있으며, 수정하는 경우 1~5점만 허용한다.
    rating = fields.Integer(
        required=False,
        validate=validate.Range(
            min=1,
            max=5,
            error="평점은 1점에서 5점 사이여야 합니다."
        )
    )

    # 리뷰 내용은 수정하지 않을 수 있으며, 수정하는 경우 최소 1글자 이상이어야 한다.
    content = fields.String(
        required=False,
        validate=validate.Length(
            min=1,
            error="리뷰 내용을 입력해주세요."
        )
    )

    @validates_schema
    def validate_update(self, data, **kwargs):
        # 수정할 필드가 하나도 없는 경우 요청을 거부한다.
        if not data:
            raise ValidationError("수정할 내용을 입력해주세요.")


class ReviewResponseSchema(Schema):
    """리뷰 응답용 스키마.

    리뷰 객체에서 클라이언트에게 반환할 필드만 정의한다.
    """

    # 리뷰 식별자
    id = fields.Integer()

    # 리뷰 작성자 식별자
    user_id = fields.Integer()

    # 리뷰가 작성된 관광 콘텐츠 식별자
    tour_content_id = fields.Integer()

    # 리뷰 평점
    rating = fields.Integer()

    # 리뷰 내용
    content = fields.String()

    # 리뷰 생성 및 수정 시간
    created_at = fields.DateTime()
    updated_at = fields.DateTime()