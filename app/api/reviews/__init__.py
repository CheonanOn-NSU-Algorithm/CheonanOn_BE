# Flask에서 Blueprint, request, jsonify를 가져온다.
# Blueprint: 리뷰 관련 API를 하나의 그룹으로 묶을 때 사용한다.
# request: 클라이언트가 보낸 데이터를 가져올 때 사용한다.
# jsonify: Python 데이터를 JSON 응답으로 만들어준다.
from flask import Blueprint, request, jsonify

# 리뷰 생성/수정 요청을 검증하기 위한 Schema를 가져온다.
from app.schemas.review import (
    ReviewCreateSchema,
    ReviewUpdateSchema,
)


# 실제 DB 작업을 담당하는 Service 함수들을 가져온다.
# API에서는 직접 DB를 조작하지 않고 Service 함수를 호출해서 DB 작업을 처리한다.
from app.services.review_service import (
    create_review,
    get_reviews_by_tour_content,
    get_review,
    update_review,
    delete_review,
)


# 리뷰 API용 Blueprint를 생성한다.
# "reviews": Blueprint의 이름이다.
# __name__: 현재 Python 파일의 모듈 이름을 전달한다.
# url_prefix="/reviews": 이 Blueprint에 등록되는 모든 URL 앞에 /reviews가 자동으로 붙는다.
review_bp = Blueprint(
    "reviews",
    __name__,
    url_prefix="/reviews"
)

# POST /reviews 요청이 들어오면 실행되는 함수
# 새로운 리뷰를 생성한다.
@review_bp.route("", methods=["POST"])
def create():

    # 리뷰 생성용 Schema 객체를 생성한다.
    schema = ReviewCreateSchema()

    # 클라이언트가 보낸 JSON 데이터를 가져온다.
    # schema.load()를 사용하면 데이터를 Python 딕셔너리로 변환하면서 Schema에 정의된 조건에 맞는지 검증한다.
    # 검증에 실패하면 Marshmallow에서 오류가 발생한다.
    data = schema.load(request.get_json())

    # 검증이 완료된 데이터를 Service에 전달한다.
    # API에서 직접 DB를 조작하지 않고 Service에게 실제 리뷰 생성 작업을 맡긴다.
    review = create_review(
        user_id=data["user_id"],
        tour_content_id=data["tour_content_id"],
        rating=data["rating"],
        content=data["content"],
    )

    # 생성된 리뷰 정보를 JSON 형태로 반환한다.
    # 201: 새로운 리소스(리뷰)가 성공적으로 생성되었다는 의미이다.
    return jsonify({
        "id": review.id,
        "user_id": review.user_id,
        "tour_content_id": review.tour_content_id,
        "rating": review.rating,
        "content": review.content,
    }), 201

# GET /reviews/tour-content/<tour_content_id> 요청이 들어오면 실행된다.
# 특정 관광 콘텐츠에 작성된 리뷰 목록을 조회한다.
@review_bp.route(
    "/tour-content/<int:tour_content_id>",
    methods=["GET"]
)
def get_by_tour_content(tour_content_id):

    # Service를 호출해서 해당 관광 콘텐츠의 리뷰 목록을 가져온다.
    reviews = get_reviews_by_tour_content(tour_content_id)

    # 여러 개의 Review 객체를 JSON 배열로 변환해서 반환한다.
    # for review in reviews: reviews에 들어있는 리뷰를 하나씩 꺼낸다.
    # 200: 정상적으로 조회되었다는 의미이다.
    return jsonify([
        {
            "id": review.id,
            "user_id": review.user_id,
            "tour_content_id": review.tour_content_id,
            "rating": review.rating,
            "content": review.content,
        }
        for review in reviews
    ]), 200


# GET /reviews/<review_id> 요청이 들어오면 실행된다.
# 특정 리뷰 하나를 조회한다.
@review_bp.route(
    "/<int:review_id>",
    methods=["GET"]
)
def get_one(review_id):

    # Service를 통해 리뷰를 조회한다.
    review = get_review(review_id)

    # 해당 ID의 리뷰가 존재하지 않는 경우
    if review is None:

        # 리뷰를 찾을 수 없다는 메시지를 JSON으로 반환한다.
        # 404: 요청한 리소스를 찾을 수 없다는 의미이다.
        return jsonify({
            "message": "리뷰를 찾을 수 없습니다."
        }), 404

    # 리뷰가 존재하면 리뷰 정보를 JSON 형태로 반환한다.
    return jsonify({
        "id": review.id,
        "user_id": review.user_id,
        "tour_content_id": review.tour_content_id,
        "rating": review.rating,
        "content": review.content,
    }), 200


# PUT /reviews/<review_id> 요청이 들어오면 실행된다.
# 기존 리뷰를 수정한다.
@review_bp.route(
    "/<int:review_id>",
    methods=["PUT"]
)
def update(review_id):

    # 리뷰 수정용 Schema 객체를 생성한다.
    schema = ReviewUpdateSchema()

    # 클라이언트가 보낸 수정 데이터를 가져온다.
    # 동시에 Schema를 이용해서 rating이 1~5 사이인지 등의 조건을 검사한다.
    data = schema.load(request.get_json())

    # Service에 리뷰 수정 작업을 요청한다.
    # data.get()을 사용했기 때문에 rating이나 content가 요청에 없더라도 None으로 처리할 수 있다.
    review = update_review(
        review_id=review_id,
        rating=data.get("rating"),
        content=data.get("content"),
    )

    # 수정할 리뷰가 존재하지 않는 경우
    if review is None:

        # 리뷰를 찾을 수 없다는 메시지를 반환한다.
        return jsonify({
            "message": "리뷰를 찾을 수 없습니다."
        }), 404

    # 수정이 완료된 리뷰 정보를 JSON 형태로 반환한다.
    return jsonify({
        "id": review.id,
        "user_id": review.user_id,
        "tour_content_id": review.tour_content_id,
        "rating": review.rating,
        "content": review.content,
    }), 200


# DELETE /reviews/<review_id> 요청이 들어오면 실행된다.
# 기존 리뷰를 삭제한다.
@review_bp.route(
    "/<int:review_id>",
    methods=["DELETE"]
)
def delete(review_id):

    # Service에 리뷰 삭제 작업을 요청한다.
    # 삭제에 성공하면 True, 해당 리뷰가 존재하지 않으면 False를 반환한다.
    result = delete_review(review_id)

    # 삭제할 리뷰가 존재하지 않는 경우
    if not result:

        # 리뷰를 찾을 수 없다는 메시지를 반환한다.
        return jsonify({
            "message": "리뷰를 찾을 수 없습니다."
        }), 404

    # 삭제가 성공했다는 메시지를 JSON으로 반환한다.
    # 200: 요청이 정상적으로 처리되었다는 의미이다.
    return jsonify({
        "message": "리뷰가 삭제되었습니다."
    }), 200