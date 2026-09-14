# auth 도메인(로그인/토큰) 담당 예외.
# 나중에 카카오 로그인 관련 예외를 추가할 때도 이 파일에 같이 두면 된다.

from app.errors.base import ApiException


class AuthException(ApiException):
    """인증 관련 예외의 상위 클래스 (401). status_code는 여기서만 정의하고
    자식 클래스들(TokenExpiredError 등)은 물려받아서 다시 안 써도 됨"""

    status_code = 401
    code = "AUTH_000"
    message = "인증에 실패했습니다."


class TokenExpiredError(AuthException):
    """JWT access/refresh 토큰이 만료됐을 때. status_code는 부모(AuthException)의
    401을 그대로 물려받고, code/message만 새로 지정"""

    code = "AUTH_001"
    message = "토큰이 만료되었습니다."
