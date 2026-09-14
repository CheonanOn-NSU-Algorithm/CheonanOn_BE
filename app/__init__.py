from flask import Flask, jsonify

from app.errors import ApiException


def create_app():
    app = Flask(__name__)

    register_error_handlers(app)

    return app


def register_error_handlers(app: Flask):
    """Spring Boot의 @RestControllerAdvice + @ExceptionHandler 역할.
    앱 전체에서 ApiException(및 그 자식 클래스들)이 raise되면 여기서 전부 잡아
    공통 JSON 포맷으로 응답한다. 팀원들은 이 함수를 건드릴 필요 없이
    error.py에 새 예외 클래스만 추가하고 raise하면 된다."""

    @app.errorhandler(ApiException)
    def handle_api_exception(e: ApiException):
        return jsonify(e.to_response()), e.status_code
