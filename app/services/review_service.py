# 리뷰(review) API의 비즈니스 로직을 정의한다.
#
# [서비스의 책임]
#   API에서 전달받은 데이터를 바탕으로
#   리뷰 생성/조회/수정/삭제 및 작성자 권한 확인을 처리한다.
#
# API 계층에서는 요청 데이터 검증과 응답 변환만 담당하고,
# 실제 DB 조회 및 변경과 리뷰 관련 비즈니스 로직은
# 이 서비스 계층에서 담당한다.
#
# [예외 처리]
#   서비스에서 발생하는 비즈니스 예외는 BusinessException으로 발생시킨다.
#   전역 예외 처리기(app/__init__.py)가 해당 예외를 받아
#   ErrorCode에 정의된 상태 코드와 메시지로 공통 응답을 반환한다.
#
#   - 리뷰가 존재하지 않는 경우
#       → REVIEW_NOT_FOUND (404)
#
#   - 리뷰 작성자가 아닌 사용자가 수정/삭제하는 경우
#       → REVIEW_FORBIDDEN (403)
#
# [현재 인증 방식]
#   JWT 인증이 아직 연결되지 않아 user_id를 서비스에 직접 전달받는다.
#   JWT 인증이 연결되면 API에서 JWT를 통해 현재 사용자의 user_id를 가져와
#   서비스에 전달하는 방식으로 변경한다.

from app.extensions import db
from app.models.review import Review
from app.errors import BusinessException, ErrorCode


def create_review(data):
    """새로운 리뷰를 생성한다.

    전달받은 요청 데이터를 Review 객체로 생성하고
    DB에 저장한 뒤 생성된 리뷰를 반환한다.

    Args:
        data: 리뷰 생성에 필요한 검증된 요청 데이터

    Returns:
        생성된 Review 객체
    """

    # 요청 데이터로 Review 객체를 생성한다.
    # 요청 데이터는 API 계층의 ReviewCreateSchema에서
    # 필수값과 평점 범위 등을 먼저 검증한다.
    review = Review(
        user_id=data["user_id"],
        tour_content_id=data["tour_content_id"],
        rating=data["rating"],
        content=data["content"],
    )

    # 생성한 리뷰를 DB 세션에 추가하고 저장한다.
    db.session.add(review)
    db.session.commit()

    return review


def get_reviews_by_tour_content(tour_content_id):
    """특정 관광 콘텐츠에 작성된 리뷰 목록을 조회한다.

    Args:
        tour_content_id: 리뷰를 조회할 관광 콘텐츠 ID

    Returns:
        해당 관광 콘텐츠에 작성된 Review 객체 목록
    """

    # 전달받은 관광 콘텐츠 ID와 일치하는 리뷰를 조회한다.
    reviews = Review.query.filter_by(
        tour_content_id=tour_content_id
    ).all()

    return reviews


def get_my_reviews(user_id):
    """특정 사용자가 작성한 리뷰 목록을 조회한다.

    현재는 JWT 인증이 연결되지 않아 API에서 전달받은
    user_id를 기준으로 리뷰를 조회한다.

    JWT 인증 연결 후에는 JWT에서 현재 사용자의 ID를 가져와
    이 서비스에 전달하게 된다.

    Args:
        user_id: 리뷰 작성자의 사용자 ID

    Returns:
        해당 사용자가 작성한 Review 객체 목록
    """

    # 전달받은 사용자 ID와 일치하는 리뷰를 조회한다.
    reviews = Review.query.filter_by(
        user_id=user_id
    ).all()

    return reviews


def update_review(review_id, user_id, data):
    """리뷰를 수정한다.

    리뷰가 존재하는지 확인하고,
    리뷰 작성자 본인인지 확인한 후 전달받은 필드만 수정한다.

    Args:
        review_id: 수정할 리뷰 ID
        user_id: 현재 사용자의 ID
        data: 검증된 리뷰 수정 데이터

    Raises:
        BusinessException:
            리뷰가 존재하지 않는 경우 REVIEW_NOT_FOUND
            리뷰 작성자가 아닌 경우 REVIEW_FORBIDDEN

    Returns:
        수정된 Review 객체
    """

    # 수정하려는 리뷰가 존재하는지 확인한다.
    review = Review.query.get(review_id)

    if review is None:
        raise BusinessException(ErrorCode.REVIEW_NOT_FOUND)

    # 리뷰 작성자 본인인지 확인한다.
    # 다른 사용자가 다른 사람의 리뷰를 수정하지 못하도록 한다.
    if review.user_id != user_id:
        raise BusinessException(ErrorCode.REVIEW_FORBIDDEN)

    # 전달받은 필드만 수정한다.
    # 따라서 rating만 보내거나 content만 보내는 부분 수정이 가능하다.
    if "rating" in data:
        review.rating = data["rating"]

    if "content" in data:
        review.content = data["content"]

    # 수정된 내용을 DB에 반영한다.
    db.session.commit()

    return review


def delete_review(review_id, user_id):
    """리뷰를 삭제한다.

    리뷰가 존재하는지 확인하고,
    리뷰 작성자 본인인지 확인한 후 해당 리뷰를 삭제한다.

    Args:
        review_id: 삭제할 리뷰 ID
        user_id: 현재 사용자의 ID

    Raises:
        BusinessException:
            리뷰가 존재하지 않는 경우 REVIEW_NOT_FOUND
            리뷰 작성자가 아닌 경우 REVIEW_FORBIDDEN

    Returns:
        삭제된 Review 객체
    """

    # 삭제하려는 리뷰가 존재하는지 확인한다.
    review = Review.query.get(review_id)

    if review is None:
        raise BusinessException(ErrorCode.REVIEW_NOT_FOUND)

    # 리뷰 작성자 본인인지 확인한다.
    # 다른 사용자가 다른 사람의 리뷰를 삭제하지 못하도록 한다.
    if review.user_id != user_id:
        raise BusinessException(ErrorCode.REVIEW_FORBIDDEN)

    # 리뷰를 DB에서 삭제한다.
    db.session.delete(review)
    db.session.commit()

    return review