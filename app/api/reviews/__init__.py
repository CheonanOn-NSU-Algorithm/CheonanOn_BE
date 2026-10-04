from flask import Blueprint


# Review API에서 사용하는 Blueprint를 생성한다.
#
# Blueprint는 여러 개의 API Route를 하나의 그룹으로 묶어 관리하기 위한 기능이다.
# Review 관련 API를 review_bp에 등록하면,
# 나중에 상위 API Blueprint에 한 번에 등록할 수 있다.
#
# url_prefix="/reviews"를 지정했기 때문에
# routes.py에서 작성하는 Route 앞에 "/reviews"가 자동으로 붙는다.
#
# 예시)
#   @review_bp.route("", methods=["POST"])
#   → POST /reviews
#
#   @review_bp.route("/my", methods=["GET"])
#   → GET /reviews/my
#
# 상위 Blueprint에서 "/api"를 사용하고 있다면
# 실제 요청 URL은 다음과 같이 된다.
#
#   POST /api/reviews
#   GET  /api/reviews/my
#
review_bp = Blueprint(
    "reviews",
    __name__,
    url_prefix="/reviews"
)


# routes.py에 작성된 Review API Route를 등록한다.
#
# review_bp만 생성해 놓으면 실제 Route가 등록되지 않기 때문에
# routes.py를 import하여 아래와 같은 Route를 등록한다.
#
#   POST   /api/reviews
#   GET    /api/reviews/tour-content/<tour_content_id>
#   GET    /api/reviews/my
#   PUT    /api/reviews/<review_id>
#   DELETE /api/reviews/<review_id>
#
from . import routes