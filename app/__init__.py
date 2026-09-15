from flask import Flask, jsonify  # Flask 앱 객체 생성, 에러 핸들러 응답용 jsonify

from app.config import Config  # JWT_SECRET_KEY, DB URI 등 환경설정 값을 담은 클래스

from app.errors import ApiException  # 공통 API 예외 베이스 클래스
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
    앱 전체에서 ApiException(및 그 자식 클래스들)이 raise되면 여기서 전부 잡아
    공통 JSON 포맷으로 응답한다. 팀원들은 이 함수를 건드릴 필요 없이
    error.py에 새 예외 클래스만 추가하고 raise하면 된다."""

    @app.errorhandler(ApiException)
    def handle_api_exception(e: ApiException):
        return jsonify(e.to_response()), e.status_code
