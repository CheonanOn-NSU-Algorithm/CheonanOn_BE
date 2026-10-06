# 행사 패키지의 진입점(entrypoint).
# 실제 Blueprint와 라우트는 routes.py에 있다. 여기서 events_bp를 다시 내보내면
# app/api/__init__.py는 routes.py의 내부 경로를 몰라도 행사 API를 등록할 수 있다.
# 이 파일을 가져올 때 routes.py도 읽히므로 @events_bp.get 라우트들이 등록된다.
from app.api.events.routes import events_bp

# `from app.api.events import *`를 쓸 때 내보낼 이름을 제한한다.
__all__ = ["events_bp"]
