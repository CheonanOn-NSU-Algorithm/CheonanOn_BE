# models 패키지의 진입점(entrypoint).
# 각 모델 모듈(user.py, token_blocklist.py 등)에 흩어진 모델 클래스를
# 여기 한 곳에 모아 import해두면, 다른 코드에서는
#   from app.models import User, TokenBlocklist
# 처럼 짧게 가져다 쓸 수 있다.
#
# 또한 Flask-Migrate(Alembic)가 마이그레이션 파일을 자동 생성(autogenerate)하려면
# db.Model을 상속한 모델 클래스들이 파이썬 프로세스에 "import되어" 있어야 하는데,
# app/__init__.py에서 `from app import models`로 이 파일을 import하는 것만으로
# 아래 두 모델이 함께 로드되게 만드는 역할도 한다.
from app.models.user import User                      # User 모델을 이 패키지 네임스페이스로 노출
from app.models.token_blocklist import TokenBlocklist  # TokenBlocklist 모델을 이 패키지 네임스페이스로 노출

# `from app.models import *` 를 했을 때 노출할 이름 목록을 명시적으로 제한
__all__ = ["User", "TokenBlocklist"]