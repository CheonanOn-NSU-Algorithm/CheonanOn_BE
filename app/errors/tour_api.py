from app.errors.base import ApiException


class TourAPIException(ApiException):
    """한국관광공사 TourAPI 연동 중 발생하는 공통 예외."""

    status_code = 400
    code = "TOUR_API_001"
    message = "TourAPI 연동 중 오류가 발생했습니다."
