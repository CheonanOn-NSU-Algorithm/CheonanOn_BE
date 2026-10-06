# 리뷰 패키지의 진입점(entrypoint).
# 실제 Blueprint와 라우트는 routes.py에 있다. 여기서 review_bp를 다시 내보내면
# app/api/__init__.py는 routes.py의 내부 경로를 몰라도 리뷰 API를 등록할 수 있다.
# 이 파일을 가져오면 routes.py도 읽히므로 @review_bp.route가 붙은 라우트들도
# Blueprint에 등록된다. 나중에 라우트 파일을 나누더라도 외부 import는 유지할 수 있다.
from app.api.reviews.routes import review_bp

# `from app.api.reviews import *`를 쓸 때 내보낼 이름을 제한한다.
__all__ = ["review_bp"]
