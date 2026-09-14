# 공통 에러 응답의 베이스 클래스.
# 이 파일은 진짜 전역(모든 도메인 공통)으로 쓰는 것만 둔다.
# 도메인별 예외(AuthException, KakaoAuthError 등)는 각자 파일(auth.py, kakao.py 등)에 둔다.


class ApiException(Exception):
    """모든 커스텀 예외의 베이스 클래스"""

    status_code = 400          # 이 예외 발생 시 응답할 HTTP 상태코드
    code = "COMMON_000"        # 프론트가 분기 처리할 때 쓰는 에러 코드
    message = "요청을 처리할 수 없습니다."  # 기본 에러 메시지

    def __init__(self, message: str | None = None):
        # raise TokenExpiredError() 처럼 인자 없이 던지면 기본 message 그대로 사용
        # raise TokenExpiredError("커스텀 메시지") 처럼 인자를 주면 그걸로 덮어씀
        super().__init__(message or self.message)
        if message:
            self.message = message

    def to_response(self) -> dict:
        # app/__init__.py의 errorhandler가 이 메서드를 호출해서 JSON 응답을 만든다
        return {
            "success": False,
            "code": self.code,
            "message": self.message,
            "status": self.status_code,
        }
