# users 패키지의 진입점(entrypoint).
# 실제 라우트는 routes.py에 있지만, 여기서 users_bp를 다시 내보내(re-export) 두면
# 다른 곳에서는 routes.py라는 내부 파일 구조를 몰라도
#     from app.api.users import users_bp
# 처럼 짧게 가져다 쓸 수 있다. (app/api/__init__.py에서 이렇게 사용 중)
from app.api.users.routes import users_bp

# `from app.api.users import *` 를 했을 때 노출할 이름을 명시적으로 제한
__all__ = ["users_bp"]
