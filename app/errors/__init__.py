# 다른 파일에서는 app.errors.base, app.errors.auth 안 쓰고
# 그냥 from app.errors import TokenExpiredError 처럼 여기서 바로 가져다 쓰면 됨.

from app.errors.base import ApiException
from app.errors.auth import AuthException, TokenExpiredError
from app.errors.tour_api import (
    TourAPIConnectionError,
    TourAPIException,
    TourAPIHTTPError,
    TourAPIInvalidResponseError,
    TourAPIKeyNotConfiguredError,
    TourAPIResponseError,
    TourAPITimeoutError,
)

__all__ = [
    "ApiException",
    "AuthException",
    "TokenExpiredError",
    "TourAPIException",
    "TourAPIKeyNotConfiguredError",
    "TourAPITimeoutError",
    "TourAPIConnectionError",
    "TourAPIHTTPError",
    "TourAPIInvalidResponseError",
    "TourAPIResponseError",
]
