# auth 패키지의 진입점(entrypoint).
# 실제 라우트는 routes.py에 있지만, 여기서 auth_bp를 다시 내보내(re-export) 두면
# 다른 곳에서는 routes.py라는 내부 파일 구조를 몰라도
#     from app.api.auth import auth_bp
# 처럼 짧게 가져다 쓸 수 있다. (app/api/__init__.py에서 이렇게 사용 중)
# 나중에 routes.py를 여러 파일로 쪼개더라도 이 파일만 고치면 바깥 코드는 영향이 없다.
from app.api.auth.routes import auth_bp

# `from app.api.auth import *` 를 했을 때 노출할 이름을 명시적으로 제한
__all__ = ["auth_bp"]
