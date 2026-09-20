from enum import Enum

"""
    작성규칙
    오류 명시 = (상태코드, 오류 메세지)

    이후 필요할 때마다 여기에 한 줄씩 추가

    - 멤버 이름(예: AUTH_TOKEN_EXPIRED)이 그대로 프론트에 내려가는 code 문자열이 된다.
      그래서 AUTH_001 같은 번호식이 아니라, 이름만 봐도 무슨 에러인지 알 수 있게 짓는다.
    - status_code를 여기(ErrorCode)에 같이 넣어두는 이유: BusinessException은 클래스가
      단 하나뿐이라서, "이 에러가 몇 번 상태코드로 응답돼야 하는지"를 클래스가 아니라
      ErrorCode가 들고 있어야 한다. 새 도메인(카카오, 유저 등)이 추가돼도 새 클래스를
      만들 필요 없이 이 enum에 멤버만 추가하면 된다.
"""
class ErrorCode(Enum):
    # --- COMMON ---
    # 도메인을 특정하기 애매한 일반적인 요청 값 오류(필수값 누락, 형식 오류 등)에 사용.
    COMMON_INVALID_INPUT = (400, "요청 값이 올바르지 않습니다.")

    # --- TOUR API ---
    TOUR_API_ERROR = (400, "TourAPI 연동 중 오류가 발생했습니다.")
    TOUR_API_KEY_MISSING = (400, "TOURAPI_KEY가 설정되지 않았습니다.")
    TOUR_API_TIMEOUT = (400, "TourAPI 응답 시간이 초과되었습니다.")
    TOUR_API_HTTP_ERROR = (400, "TourAPI가 요청 처리에 실패했습니다.")
    TOUR_API_CONNECTION_ERROR = (400, "TourAPI에 연결할 수 없습니다.")
    TOUR_API_INVALID_RESPONSE = (400, "TourAPI에서 올바르지 않은 응답을 받았습니다.")
    TOUR_API_RESULT_ERROR = (400, "TourAPI 요청 결과가 실패로 반환되었습니다.")
    TOUR_INVALID_CONTENT_TYPE = (400, "지원하지 않는 관광 콘텐츠 타입입니다.")
    TOUR_FESTIVAL_DATES_REQUIRED = (400, "축제 조회 시작일과 종료일을 모두 입력해주세요.")
    TOUR_FESTIVAL_INVALID_DATE = (400, "축제 조회 날짜는 YYYYMMDD 형식으로 입력해주세요.")
    TOUR_FESTIVAL_INVALID_RANGE = (400, "축제 조회 시작일은 종료일보다 늦을 수 없습니다.")

    # --- AUTH ---
    # 로그인 자체가 안 됐거나 인증 수단이 아예 없는 등, 원인을 세분화하지 않은 일반 인증 실패.
    # (토큰이 "없는" 것과 "만료된" 것을 구분해야 하면 별도 ErrorCode를 추가해서 쓴다.)
    AUTH_UNAUTHORIZED = (401, "인증에 실패했습니다.")

    # --- JWT ---
    # access/refresh 토큰의 유효기간(exp)이 지나서 더 이상 사용할 수 없을 때.
    # 프론트에서는 이 code를 보고 리프레시 토큰으로 재발급을 시도하거나 재로그인시키면 된다.
    AUTH_TOKEN_EXPIRED = (401, "토큰이 만료되었습니다.")

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

    @property
    def code(self) -> str:
        # enum 멤버 이름(예: "AUTH_TOKEN_EXPIRED")을 그대로 응답의 code 값으로 사용.
        # BusinessException.error_code.code 로 접근해서 CommonResponse.error()에 전달된다.
        return self.name
