# 북마크 패키지의 진입점. 실제 Blueprint와 라우트는 routes.py에 정의한다.
# app/api/__init__.py에서는 다른 도메인과 같은 방식으로 bookmark_bp를 가져온다.
from app.api.bookmarks.routes import bookmark_bp

# 패키지에서 외부로 공개할 Blueprint 이름을 제한한다.
__all__ = ["bookmark_bp"]
