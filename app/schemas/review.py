from marshmallow import (
    Schema,
    fields,
    validate,
    validates_schema,
    ValidationError,
)


# 리뷰 API의 요청 및 응답 데이터 형식을 정의하는 Schema 모듈이다.
#
# [Schema의 역할]
# - API 요청 데이터의 필드와 타입을 정의한다.
# - 리뷰 생성 및 수정 요청값을 검증한다.
# - 잘못된 요청값이 전달되면 ValidationError를 발생시킨다.
# - DB의 Review 객체를 API 응답 형식으로 변환한다.
#
# [Schema와 다른 계층의 역할]
#
# - routes.py
#   · HTTP 요청 수신
#   · JWT 인증
#   · Schema를 통한 요청값 검증
#   · Service 호출
#   · API 응답 반환
#
# - Schema
#   · 요청 데이터의 형식 및 입력값 검증
#   · 응답 데이터의 형식 정의
#
# - review_service.py
#   · DB 조회 및 변경
#   · 리뷰 생성, 조회, 수정, 삭제
#   · 작성자 권한 확인
#   · 평균 평점 계산
#
# [주요 Schema]
#
# - ReviewCreateSchema
#   → 리뷰 생성 요청 데이터를 검증한다.
#
# - ReviewUpdateSchema
#   → 리뷰 수정 요청 데이터를 검증한다.
#
# - ReviewResponseSchema
#   → Review 객체를 API 응답 형식으로 변환한다.
#
# [평점 검증]
# 리뷰 평점은 0.5 ~ 5.0 범위에서
# 0.5 단위로만 입력할 수 있다.
#
# 예:
#   0.5, 1.0, 1.5, 2.0, ... , 4.5, 5.0
#
# 잘못된 값:
#   0.4, 1.2, 3.7, 5.5


# 평점 입력값을 검증한다.
#
# 검증 조건:
# - 0.5점 이상 5점 이하
# - 0.5점 단위로 입력
#
# ReviewCreateSchema와 ReviewUpdateSchema에서
# rating 필드의 validate 옵션으로 사용한다.
def validate_rating(value):
    # 평점의 최소 및 최대 범위를 검사한다.
    if value < 0.5 or value > 5:
        raise ValidationError()

    # 평점이 0.5점 단위인지 검사한다.
    #
    # 0.5 단위의 숫자는 2를 곱하면 정수가 된다.
    #
    # 예:
    #   4.5 × 2 = 9   → 정상
    #   4.0 × 2 = 8   → 정상
    #   4.3 × 2 = 8.6 → 오류
    if value * 2 != int(value * 2):
        raise ValidationError()


# 리뷰 생성 요청 Schema
#
# 리뷰 생성에 필요한 필드와 입력 조건을 정의한다.
#
# user_id는 요청으로 받지 않는다.
# 로그인한 사용자의 ID는 JWT에서 가져와
# routes.py에서 Service로 전달한다.
class ReviewCreateSchema(Schema):

    # 리뷰가 작성될 관광 콘텐츠의 ID
    tour_content_id = fields.Integer(
        required=True
    )

    # 리뷰 평점
    #
    # 0.5 ~ 5.0 범위에서
    # 0.5 단위로 입력할 수 있다.
    rating = fields.Float(
        required=True,
        validate=validate_rating,
    )

    # 리뷰 내용
    #
    # 반드시 입력해야 하며
    # 최소 1글자 이상이어야 한다.
    content = fields.String(
        required=True,
        validate=validate.Length(
            min=1
        )
    )


# 리뷰 수정 요청 Schema
#
# rating과 content를 선택적으로 수정할 수 있다.
#
# 예:
# {
#     "rating": 4.5
# }
#
# {
#     "content": "수정된 리뷰입니다."
# }
#
# {
#     "rating": 4.5,
#     "content": "수정된 리뷰입니다."
# }
class ReviewUpdateSchema(Schema):

    # 수정할 평점
    #
    # 전달된 경우에만
    # 0.5 ~ 5.0 범위와 0.5 단위 여부를 검사한다.
    rating = fields.Float(
        required=False,
        validate=validate_rating,
    )

    # 수정할 리뷰 내용
    #
    # 전달된 경우 최소 1글자 이상이어야 한다.
    content = fields.String(
        required=False,
        validate=validate.Length(
            min=1
        )
    )

    # 수정할 데이터가 최소 하나 이상 전달되었는지 확인한다.
    #
    # rating과 content가 모두 required=False이므로
    # 빈 객체 {}도 기본적으로 Schema를 통과할 수 있다.
    #
    # 따라서 수정할 내용이 없는 요청을 별도로 검사한다.
    @validates_schema
    def validate_update(self, data, **kwargs):

        # 수정할 필드가 하나도 전달되지 않은 경우
        # ValidationError를 발생시킨다.
        if not data:
            raise ValidationError()


# 리뷰 응답 Schema
#
# DB에서 조회한 Review 객체를
# API 응답 JSON 형식으로 변환할 때 사용한다.
#
# ReviewResponseSchema().dump(review)
# 또는
# ReviewResponseSchema(many=True).dump(reviews)
# 형태로 사용한다.
class ReviewResponseSchema(Schema):

    # 리뷰 ID
    id = fields.Integer()

    # 리뷰 작성자 ID
    user_id = fields.Integer()

    # 관광 콘텐츠 ID
    tour_content_id = fields.Integer()

    # 리뷰 평점
    #
    # 0.5 단위의 값을 반환하기 위해 Float를 사용한다.
    rating = fields.Float()

    # 리뷰 내용
    content = fields.String()

    # 리뷰 생성 시간
    created_at = fields.DateTime()

    # 리뷰 수정 시간
    updated_at = fields.DateTime()