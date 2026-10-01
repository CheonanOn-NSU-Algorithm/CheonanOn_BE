# 리뷰(review) 관련 API 라우트 모음. (Spring의 ReviewController 역할)
#
# [라우트(컨트롤러)의 책임은 딱 3가지]
#   1) 요청 값 검증 : 스키마(app/schemas/review.py)의 load()로 요청 데이터를 검사
#   2) 서비스 호출  : 실제 리뷰 생성/조회/수정/삭제 로직은
#                     app/services/review_service.py에 맡긴다.
#   3) 응답 만들기  : ResponseSchema로 필요한 필드만 추려
#                     CommonResponse.success()로 공통 응답 형식에 담아 반환한다.
#
# → DB 조회/수정/삭제, 작성자 권한 확인 등의 비즈니스 로직은
#   이 파일에서 직접 처리하지 않는다.
#
# [예외 처리]
#   이 라우트에서 발생한 예외는 직접 try/except로 처리하지 않고
#   전역 예외 처리기가 공통 JSON 응답으로 변환한다.
#
#   - 스키마 검증 실패(ValidationError)
#       → app/__init__.py 핸들러
#       → 400 COMMON_INVALID_INPUT
#
#   - 리뷰가 존재하지 않는 경우
#       → review_service.py에서 BusinessException 발생
#       → 404 REVIEW_NOT_FOUND
#
#   - 리뷰 작성자가 아닌 사용자가 수정/삭제하는 경우
#       → review_service.py에서 BusinessException 발생
#       → 403 REVIEW_FORBIDDEN
#
#   - 그 외 예상하지 못한 예외
#       → app/__init__.py의 전역 Exception 핸들러
#       → 500 COMMON_INTERNAL_ERROR
#
# [현재 인증 방식]
#   JWT 인증이 아직 연결되지 않은 상태이므로
#   임시로 user_id를 요청 파라미터에서 받아 사용한다.
#
#   JWT 인증이 연결되면 user_id를 클라이언트가 전달하지 않고
#   JWT의 사용자 정보에서 가져오도록 변경한다.

from flask import Blueprint, request, jsonify

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
    update_review,
    delete_review,
)


# url_prefix="/reviews"를 사용하여
# 이 Blueprint에 등록되는 모든 리뷰 API의 기본 경로를 지정한다.
review_bp = Blueprint(
    "reviews",
    __name__,
    url_prefix="/reviews"
)


@review_bp.route("", methods=["POST"])
def create():
    """리뷰 생성.

    POST /reviews

    요청 body:
        {
            "user_id": 1,
            "tour_content_id": 1,
            "rating": 5,
            "content": "정말 좋은 축제였습니다."
        }

    성공 응답:
        201 Created

    실패 응답:
        400 COMMON_INVALID_INPUT
    """

    # request body를 ReviewCreateSchema로 검증한다.
    # 필수값 누락이나 평점 범위 오류 등이 발생하면
    # ValidationError가 발생하고 전역 예외 처리기가 400으로 변환한다.
    data = ReviewCreateSchema().load(
        request.get_json(silent=True) or {}
    )

    # 검증된 데이터를 서비스 계층에 전달하여 리뷰를 생성한다.
    result = create_review(data)

    # 생성된 Review 객체를 응답 스키마를 통해
    # 클라이언트에 필요한 필드만 반환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 201


@review_bp.route("/tour-content/<int:tour_content_id>", methods=["GET"])
def get_by_tour_content(tour_content_id):
    """특정 관광 콘텐츠의 리뷰 목록 조회.

    GET /reviews/tour-content/{tour_content_id}
    """

    # 관광 콘텐츠 ID를 서비스에 전달하여
    # 해당 콘텐츠에 작성된 리뷰 목록을 조회한다.
    result = get_reviews_by_tour_content(tour_content_id)

    # 여러 개의 Review 객체를 응답 스키마로 변환한다.
    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema(many=True).dump(result)
        )
    ), 200


@review_bp.route("/my", methods=["GET"])
def get_my():
    """현재 사용자가 작성한 리뷰 목록 조회.

    GET /reviews/my?user_id={user_id}

    현재는 JWT 인증이 연결되지 않아
    임시로 query parameter에서 user_id를 전달받는다.
    """

    # 현재 로그인한 사용자의 ID를 가져온다.
    # JWT 인증 연결 후에는 get_jwt_identity() 등으로 변경한다.
    user_id = request.args.get("user_id", type=int)

    # 해당 사용자가 작성한 리뷰를 조회한다.
    result = get_my_reviews(user_id)

    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema(many=True).dump(result)
        )
    ), 200


@review_bp.route("/<int:review_id>", methods=["PUT"])
def update(review_id):
    """리뷰 수정.

    PUT /reviews/{review_id}?user_id={user_id}

    평점 또는 리뷰 내용 중 수정할 필드만 전달할 수 있다.
    """

    # 수정할 데이터가 있는지와 각 필드의 값이 올바른지 검사한다.
    # 빈 {} 요청은 ReviewUpdateSchema에서 검증 실패한다.
    data = ReviewUpdateSchema().load(
        request.get_json(silent=True) or {}
    )

    # 현재 사용자의 ID를 가져온다.
    # JWT 인증 연결 후에는 토큰에서 사용자 ID를 가져오도록 변경한다.
    user_id = request.args.get("user_id", type=int)

    # 리뷰 존재 여부와 작성자 권한을 확인한 뒤 리뷰를 수정한다.
    result = update_review(
        review_id,
        user_id,
        data
    )

    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 200


@review_bp.route("/<int:review_id>", methods=["DELETE"])
def delete(review_id):
    """리뷰 삭제.

    DELETE /reviews/{review_id}?user_id={user_id}
    """

    # 현재 사용자의 ID를 가져온다.
    # JWT 인증 연결 후에는 토큰에서 사용자 ID를 가져오도록 변경한다.
    user_id = request.args.get("user_id", type=int)

    # 리뷰 존재 여부와 작성자 권한을 확인한 뒤 리뷰를 삭제한다.
    result = delete_review(
        review_id,
        user_id
    )

    return jsonify(
        CommonResponse.success(
            ReviewResponseSchema().dump(result)
        )
    ), 200