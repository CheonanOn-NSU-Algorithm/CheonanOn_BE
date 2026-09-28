# SQLAlchemy의 DB 객체를 가져온다.
from app.extensions import db

# 우리가 만든 Review 모델을 가져온다.
# 실제 리뷰 데이터를 DB에 저장하거나 조회할 때 사용한다.
from app.models.review import Review


# 새로운 리뷰를 생성하는 함수
# API에서 전달받은 값을 이용해서 Review 객체를 만든다.
def create_review(user_id, tour_content_id, rating, content):

    # Review 객체를 생성한다.
    # 아직 DB에 실제로 저장된 것은 아니다.
    review = Review(
        user_id=user_id,
        tour_content_id=tour_content_id,
        rating=rating,
        content=content,
    )

    # SQLAlchemy 세션에 리뷰를 추가한다.
    # DB에 저장할 준비를 하는 과정이다.
    db.session.add(review)

    # 변경사항을 실제 DB에 반영한다.
    # commit()이 실행되어야 INSERT가 DB에 반영된다.
    db.session.commit()

    # 저장된 Review 객체를 API 쪽으로 반환한다.
    return review


# 특정 관광 콘텐츠에 작성된 리뷰를
# 모두 가져오는 함수
# 특정 행사에 작성된 모든 리뷰를 조회한다.
def get_reviews_by_tour_content(tour_content_id):
    # 전달받은 행사 ID와 일치하는 리뷰를 모두 조회한다.
    return Review.query.filter_by(
        tour_content_id=tour_content_id
    ).all()


# 특정 사용자가 작성한 모든 리뷰를 조회한다.
def get_my_reviews(user_id):
    # 전달받은 사용자 ID와 일치하는 리뷰를 모두 조회한다.
    return Review.query.filter_by(
        user_id=user_id
    ).all()


# 기존 리뷰를 수정하는 함수
# rating과 content는 선택적으로 받을 수 있다.
def update_review(review_id, rating=None, content=None):

    # 수정할 리뷰를 DB에서 찾는다.
    review = Review.query.get(review_id)

    # 해당 ID의 리뷰가 존재하지 않는 경우
    if review is None:

        # API에서 404 응답을 만들 수 있도록
        # None을 반환한다.
        return None

    # rating 값이 전달된 경우에만
    # 기존 평점을 새로운 평점으로 변경한다.
    if rating is not None:
        review.rating = rating

    # content 값이 전달된 경우에만
    # 기존 리뷰 내용을 새로운 내용으로 변경한다.
    if content is not None:
        review.content = content

    # 수정된 내용을 실제 DB에 반영한다.
    db.session.commit()

    # 수정된 Review 객체를 반환한다.
    return review


# 리뷰 하나를 삭제하는 함수
def delete_review(review_id):

    # 삭제할 리뷰를 DB에서 먼저 조회한다.
    review = Review.query.get(review_id)

    # 해당 ID의 리뷰가 존재하지 않는 경우
    if review is None:

        # 삭제할 대상이 없다는 의미로 False를 반환한다.
        return False

    # 해당 리뷰를 삭제할 준비를 한다.
    db.session.delete(review)

    # 실제 DB에서 리뷰를 삭제한다.
    db.session.commit()

    # 삭제가 성공했다는 의미로 True를 반환한다.
    return True