from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.common_response import CommonResponse
from app.schemas.review import (
    ReviewCreateSchema,
    ReviewUpdateSchema,
    ReviewResponseSchema,
)
from app.services.review_service import (
    create_review,
    get_reviews_by_tour_content,
    get_my_reviews,
    get_rating_info,
    update_review,
    delete_review,
)
from . import review_bp


# 리뷰 API의 HTTP 요청과 응답을 처리하는 라우트 모듈이다.
#
# [라우트의 역할]
# - HTTP 요청을 받아 필요한 데이터를 추출한다.
# - JWT 인증을 처리하고 현재 사용자의 ID를 확인한다.
# - Schema를 사용하여 요청 데이터를 검증한다.
# - Service의 비즈니스 로직을 호출한다.
# - 처리 결과를 Schema와 CommonResponse를 사용하여
#   공통 JSON 응답 형식으로 반환한다.
#
# [사용하는 주요 함수]
# - jwt_required()
#   → API 요청에 JWT 인증이 필요한 경우 사용한다.
#
# - get_jwt_identity()
#   → JWT에 저장된 현재 사용자의 ID를 가져온다.
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
# - create_review()
#   → 새로운 리뷰를 생성한다.
#
# - get_reviews_by_tour_content()
#   → 특정 관광 콘텐츠의 리뷰 목록을 조회한다.
#
# - get_my_reviews()
#   → 현재 사용자가 작성한 리뷰 목록을 조회한다.
#
# - get_rating_info()
#   → 평균 평점과 리뷰 개수를 조회한다.
#
# - update_review()
#   → 리뷰를 수정한다.
#
# - delete_review()
#   → 리뷰를 삭제한다.
#
# - CommonResponse.success()
#   → API의 성공 응답을 공통 형식으로 만든다.
#
# [API 호출 공통 사항]
# - 모든 리뷰 API는 JWT 인증이 필요하다.
# - Authorization 헤더에 Access Token을 포함해야 한다.
#
# Authorization: Bearer <access_token>


# 리뷰 생성
@review_bp.route("", methods=["POST"])
@jwt_required()
def create():
    """새로운 리뷰를 생성한다.

    호출 예시:
    POST /api/reviews
    Authorization: Bearer <access_token>

    {
        "tour_content_id": 1,
        "rating": 4.5,
        "content": "관광지가 정말 좋았습니다."
    }
    """

    # JWT에서 현재 로그인한 사용자의 ID를 가져온다.
    user_id = int(get_jwt_identity())

    # 요청 데이터를 검증한다.
    data = ReviewCreateSchema().load(
        request.get_json(silent=True) or {}
    )

    # JWT에서 확인한 user_id를 리뷰 데이터에 추가한다.
    data["user_id"] = user_id

    # 리뷰 생성 Service를 호출한다.
    result = create_review(data)

    # 생성된 리뷰를 응답 형식으로 변환하여 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 201


# 특정 관광 콘텐츠의 리뷰 목록 조회
@review_bp.route(
    "/tour-content/<int:tour_content_id>",
    methods=["GET"]
)
@jwt_required()
def get_by_tour_content(tour_content_id):
    """특정 관광 콘텐츠의 리뷰 목록을 조회한다.

    호출 예시:
    GET /api/reviews/tour-content/1
    Authorization: Bearer <access_token>
    """

    # 특정 관광 콘텐츠의 리뷰 목록을 조회한다.
    result = get_reviews_by_tour_content(
        tour_content_id
    )

    # 조회된 리뷰 목록을 응답 형식으로 변환하여 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema(many=True).dump(result)
        )
    ), 200


# 특정 관광 콘텐츠의 평균 평점 및 리뷰 개수 조회
@review_bp.route(
    "/tour-content/<int:tour_content_id>/rating",
    methods=["GET"]
)
@jwt_required()
def get_average_rating_by_tour_content(tour_content_id):
    """특정 관광 콘텐츠의 평균 평점과 리뷰 개수를 조회한다.

    호출 예시:
    GET /api/reviews/tour-content/1/rating
    Authorization: Bearer <access_token>
    """

    # 평균 평점과 리뷰 개수를 조회한다.
    rating_info = get_rating_info(
        tour_content_id
    )

    # 조회 결과를 공통 응답 형식으로 반환한다.
    return jsonify(
        CommonResponse.success({
            "tour_content_id": tour_content_id,
            "average_rating": rating_info["average_rating"],
            "review_count": rating_info["review_count"],
        })
    ), 200


# 내가 작성한 리뷰 목록 조회
@review_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my():
    """현재 로그인한 사용자가 작성한 리뷰 목록을 조회한다.

    호출 예시:
    GET /api/reviews/my
    Authorization: Bearer <access_token>
    """

    # JWT에서 현재 로그인한 사용자의 ID를 가져온다.
    user_id = int(get_jwt_identity())

    # 현재 사용자가 작성한 리뷰를 조회한다.
    result = get_my_reviews(user_id)

    # 조회된 리뷰 목록을 응답 형식으로 변환하여 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema(many=True).dump(result)
        )
    ), 200


# 리뷰 수정
@review_bp.route("/<int:review_id>", methods=["PUT"])
@jwt_required()
def update(review_id):
    """본인이 작성한 리뷰를 수정한다.

    호출 예시:
    PUT /api/reviews/1
    Authorization: Bearer <access_token>

    {
        "rating": 4.5,
        "content": "수정된 리뷰 내용입니다."
    }
    """

    # JWT에서 현재 로그인한 사용자의 ID를 가져온다.
    user_id = int(get_jwt_identity())

    # 요청 데이터를 검증한다.
    data = ReviewUpdateSchema().load(
        request.get_json(silent=True) or {}
    )

    # 리뷰 수정 Service를 호출한다.
    result = update_review(
        review_id,
        user_id,
        data
    )

    # 수정된 리뷰를 응답 형식으로 변환하여 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 200


# 리뷰 삭제
@review_bp.route("/<int:review_id>", methods=["DELETE"])
@jwt_required()
def delete(review_id):
    """본인이 작성한 리뷰를 삭제한다.

    호출 예시:
    DELETE /api/reviews/1
    Authorization: Bearer <access_token>
    """

    # JWT에서 현재 로그인한 사용자의 ID를 가져온다.
    user_id = int(get_jwt_identity())

    # 리뷰 삭제 Service를 호출한다.
    result = delete_review(
        review_id,
        user_id
    )

    # 삭제된 리뷰를 응답 형식으로 변환하여 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 200