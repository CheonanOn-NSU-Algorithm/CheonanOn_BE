from flask import Flask, jsonify  # Flask 앱 객체 생성, 에러 핸들러 응답용 jsonify

from app.config import Config  # JWT_SECRET_KEY, DB URI 등 환경설정 값을 담은 클래스

from app.errors import BusinessException, ErrorCode  # 공통 비지니스 예외 클래스
from app.common_response import CommonResponse  # 공통 응답 반환
from werkzeug.exceptions import HTTPException

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
    앱 전체에서 발생하는 예외를 라우트마다 try/except로 잡지 않고 여기 한 곳에서
    전부 공통 JSON 포맷으로 응답한다. Flask는 raise된 예외의 타입과 가장 가까운
    @app.errorhandler를 자동으로 찾아 호출해주기 때문에, 등록 순서는 상관없다.

    아래 3개 핸들러는 "얼마나 예상된 예외인가" 순으로 안전망이 겹쳐 있다.
    1) BusinessException : 우리가 의도적으로 raise하는 비즈니스 실패 케이스.
       새 실패 케이스가 생겨도 이 함수나 새 예외 클래스를 추가할 필요 없이
       app/errors/codes.py의 ErrorCode에 멤버 하나만 추가하고
       raise BusinessException(ErrorCode.그_멤버)만 하면 된다.
    2) HTTPException : 존재하지 않는 라우트(404), 잘못된 HTTP 메서드(405) 등
       Flask/Werkzeug가 라우팅 단계에서 자체적으로 던지는 예외.
    3) Exception : 위 두 경우로 못 거른, 코드 버그나 외부 API 실패 등
       예상 못한 모든 예외를 잡는 최종 안전망. 이게 없으면 이런 예외는
       그대로 500으로 터지면서 우리 공통 응답 포맷을 벗어난다."""

    @app.errorhandler(BusinessException)
    def handle_business_exception(e: BusinessException):
        # e.status_code / e.error_code 둘 다 BusinessException이 아니라 e.error_code(ErrorCode)에서
        # 정해진 값이다 (app/errors/exception.py, app/errors/codes.py 참고).
        return jsonify(CommonResponse.error(e.error_code, e.message, e.extra)), e.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        # 404, 405 같은 라우팅 단계 오류. ErrorCode가 없어서 CommonResponse.error()로는
        # 못 만들고, HTTPException이 이미 들고 있는 code/name/description으로 직접 구성한다.
        return jsonify({"success": False, "code": e.name, "message": e.description}), e.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e: Exception):
        # BusinessException도, HTTPException도 아닌 그 외 모든 예외(코드 버그,
        # DB/외부 API 호출 중 발생한 미처리 예외 등)를 여기서 최종적으로 잡는다.
        # error()가 아니라 exception()을 써야 스택트레이스까지 로그에 남아서
        # 운영 중 500 에러의 원인을 코드 위치까지 추적할 수 있다.
        app.logger.exception(e)
        # 실제 원인(e)은 로그로만 남기고, 응답에는 노출하지 않는다.
        # 클라이언트에는 항상 동일한 일반 메시지(COMMON_INTERNAL_ERROR)만 내려준다.
        return jsonify(CommonResponse.error(ErrorCode.COMMON_INTERNAL_ERROR)), 500
