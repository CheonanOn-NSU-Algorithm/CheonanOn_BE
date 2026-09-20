from flask import Flask, jsonify  # Flask 앱 객체 생성, 에러 핸들러 응답용 jsonify

from app.config import Config  # JWT_SECRET_KEY, DB URI 등 환경설정 값을 담은 클래스

from app.errors import BusinessException # 공통 비지니스 예외 클래스
from app.common_response import CommonResponse  # 공통 응답 반환

from app.extensions import db, migrate, jwt  # DB/마이그레이션/JWT 확장 객체 (app에 바인딩할 예정)
# models 패키지를 import해서 User, TokenBlocklist 등 모델 클래스들을 로드시킴.
# 이 코드에서 직접 모델을 쓰지는 않지만, Flask-Migrate가 마이그레이션을 자동 생성할 때
# db.Model을 상속한 클래스들이 이미 import되어 있어야 인식할 수 있기 때문에 필요하다.
from app import models

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)  # Config 클래스의 설정값들을 app.config에 적용

    db.init_app(app)          # extensions.py에서 만든 db 객체를 이 app에 연결
    migrate.init_app(app, db) # Alembic 마이그레이션이 이 app/db 조합을 쓰도록 연결
    jwt.init_app(app)         # JWT 인증 기능을 이 app에 연결

    register_error_handlers(app)  # ApiException 공통 에러 핸들러 등록

    return app


def register_error_handlers(app: Flask):
    """Spring Boot의 @RestControllerAdvice + @ExceptionHandler 역할.
    앱 전체에서 BusinessException이 raise되면 여기서 전부 잡아 공통 JSON 포맷으로 응답한다.

    예외 클래스는 BusinessException 하나뿐이라서, 새로운 실패 케이스가 생겨도
    이 함수나 새 예외 클래스를 추가할 필요 없이 app/errors/codes.py의 ErrorCode에
    멤버 하나만 추가하고 raise BusinessException(ErrorCode.그_멤버)만 하면 된다."""

    @app.errorhandler(BusinessException)
    def handle_business_exception(e: BusinessException):
        # e.status_code / e.error_code 둘 다 BusinessException이 아니라 e.error_code(ErrorCode)에서
        # 정해진 값이다 (app/errors/exception.py, app/errors/codes.py 참고).
        return jsonify(CommonResponse.error(e.error_code, e.message, e.extra)), e.status_code
