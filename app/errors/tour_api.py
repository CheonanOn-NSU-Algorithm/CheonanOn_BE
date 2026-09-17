from app.errors.base import ApiException


class TourAPIException(ApiException):
    """한국관광공사 TourAPI 연동 관련 예외의 상위 클래스"""

    status_code = 500
    code = "TOUR_API_000"
    message = "TourAPI 연동 중 오류가 발생했습니다."


class TourAPIKeyNotConfiguredError(TourAPIException):
    """TourAPI 인증키가 서버 환경변수에 설정되지 않은 경우"""

    code = "TOUR_API_001"
    message = "TOURAPI_KEY가 설정되지 않았습니다."


class TourAPITimeoutError(TourAPIException):
    """TourAPI가 제한 시간 안에 응답하지 않은 경우"""

    status_code = 504
    code = "TOUR_API_002"
    message = "TourAPI 응답 시간이 초과되었습니다."


class TourAPIConnectionError(TourAPIException):
    """네트워크 문제로 TourAPI에 연결하지 못한 경우"""

    status_code = 502
    code = "TOUR_API_003"
    message = "TourAPI에 연결할 수 없습니다."


class TourAPIHTTPError(TourAPIException):
    """TourAPI가 성공이 아닌 HTTP 상태 코드로 응답한 경우"""

    status_code = 502
    code = "TOUR_API_004"
    message = "TourAPI가 요청 처리에 실패했습니다."


class TourAPIInvalidResponseError(TourAPIException):
    """TourAPI 응답이 JSON이 아니거나 예상한 구조와 다른 경우"""

    status_code = 502
    code = "TOUR_API_005"
    message = "TourAPI에서 올바르지 않은 응답을 받았습니다."


class TourAPIResponseError(TourAPIException):
    """TourAPI 응답의 결과 코드가 실패를 나타내는 경우"""

    status_code = 502
    code = "TOUR_API_006"
    message = "TourAPI 요청 결과가 실패로 반환되었습니다."
