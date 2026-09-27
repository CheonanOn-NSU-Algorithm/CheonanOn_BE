# Marshmallow의 기본 Schema 클래스와
# 데이터 타입을 정의할 때 사용하는 fields, 값의 범위를 검증할 때 사용하는 validate를 가져온다.
from marshmallow import Schema, fields, validate

# 리뷰 생성(POST)에 사용할 데이터 형식을 정의하는 Schema
class ReviewCreateSchema(Schema):

    # 리뷰를 작성하는 사용자의 ID
    # Integer → 정수형 데이터
    # required=True → 반드시 요청 데이터에 포함되어야 함
    user_id = fields.Integer(required=True)

    # 리뷰를 작성할 축제/관광 콘텐츠의 ID
    # 반드시 전달되어야 하는 값
    tour_content_id = fields.Integer(required=True)

    # 리뷰 평점
    # 1~5 사이의 정수만 허용한다.
    rating = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=5)
    )

    # 리뷰 내용
    # 문자열(String) 형태이며 반드시 입력해야 한다.
    content = fields.String(required=True)

# 리뷰 수정(PUT)에 사용할 데이터 형식을 정의하는 Schema
class ReviewUpdateSchema(Schema):

    # 수정할 평점
    # required=False 평점을 수정하지 않아도 된다.
    # 단, 값을 입력한다면 1~5 사이의 값이어야 한다.
    rating = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=5)
    )

    # 수정할 리뷰 내용
    # required=False 내용은 수정하지 않아도 된다.
    content = fields.String(required=False)