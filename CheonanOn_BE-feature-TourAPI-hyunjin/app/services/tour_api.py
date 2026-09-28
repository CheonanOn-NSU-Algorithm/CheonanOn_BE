# 한국관광공사 API 호출과 응답 형식 검증을 담당한다. DB 저장은 tour_sync.py에서 한다.

import re
from datetime import datetime, timedelta, timezone

import requests

from app.config import Config
from app.errors import BusinessException, ErrorCode

KST = timezone(timedelta(hours=9))


def iter_pages(api, endpoint, params):
    # 첫 응답의 totalCount를 기준으로 모든 페이지를 읽는다.
    # 수집 도중 페이지가 반복되거나 일부가 빠지면 조용히 성공 처리하지 않고 오류로 알린다.
    page, received, expected = 1, 0, None
    seen = set()
    while True:
        data = api.request(endpoint, {**params, "pageNo": page, "numOfRows": 100})
        items = api.get_items(data)
        total_text = str(data["response"]["body"].get("totalCount", ""))
        if not re.fullmatch(r"[0-9]+", total_text):
            raise ValueError(f"{endpoint} page={page}: totalCount 오류")
        total = int(total_text)
        if expected is not None and total != expected:
            raise ValueError(f"{endpoint} page={page}: 수집 중 totalCount 변경")
        expected = total
        if any(not isinstance(item, dict) for item in items):
            raise ValueError(f"{endpoint} page={page}: 항목 형식 오류")
        fingerprint = repr(items)
        # API가 같은 페이지를 계속 돌려주면 무한 루프가 될 수 있어 응답 내용을 비교한다.
        if items and fingerprint in seen:
            raise ValueError(f"{endpoint} page={page}: 동일 페이지 반복")
        seen.add(fingerprint)
        if not items and received < total:
            raise ValueError(f"{endpoint} page={page}: 조기 빈 응답")
        received += len(items)
        if received > total:
            raise ValueError(f"{endpoint} page={page}: totalCount 초과")
        yield page, items
        if received == total:
            return
        page += 1


class TourAPI:
    # 호출자가 API 키나 HTTP 세부사항을 몰라도 축제 데이터를 조회할 수 있게 한다.

    def __init__(self):
        if not Config.TOURAPI_KEY:
            raise BusinessException(ErrorCode.TOUR_API_KEY_MISSING)
        self.api_key = requests.utils.unquote(Config.TOURAPI_KEY)
        self.api_base_url = "https://apis.data.go.kr/B551011/KorService2"
        self.default_params = {
            "serviceKey": self.api_key,
            "MobileOS": "ETC",
            "MobileApp": "MyTourApp",
            "_type": "json",
        }

    def request(self, endpoint, params=None):
        # 모든 엔드포인트에 필요한 인증·기기 파라미터에 호출별 파라미터를 합친다.
        request_params = {**self.default_params, **(params or {})}
        try:
            response = requests.get(
                f"{self.api_base_url}/{endpoint}", params=request_params, timeout=10
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as error:
            raise BusinessException(ErrorCode.TOUR_API_TIMEOUT) from error
        except requests.exceptions.HTTPError as error:
            raise BusinessException(ErrorCode.TOUR_API_HTTP_ERROR) from error
        except requests.exceptions.RequestException as error:
            raise BusinessException(ErrorCode.TOUR_API_CONNECTION_ERROR) from error
        try:
            data = response.json()
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE) from error
        api_response = data.get("response") if isinstance(data, dict) else None
        header = api_response.get("header") if isinstance(api_response, dict) else None
        if not isinstance(header, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)
        if str(header.get("resultCode", "")) != "0000":
            raise BusinessException(ErrorCode.TOUR_API_RESULT_ERROR)
        return data

    @staticmethod
    def get_items(data):
        # 결과가 0건일 때 items가 빈 값인 응답과 형식이 잘못된 응답을 구분한다.
        try:
            body = data["response"]["body"]
            items = body.get("items", {})
            if not items:
                return []
            result = items["item"]
            if not isinstance(result, list):
                raise TypeError()
            return result
        except (KeyError, TypeError, AttributeError) as error:
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE) from error

    @staticmethod
    def validate_festival_dates(start_date=None, end_date=None):
        if start_date is None and end_date is None:
            # 기본 기간은 KST 기준 이번 달 1일에서 다음 해 같은 달 1일 직전까지다.
            now = datetime.now(KST)
            start = now.date().replace(day=1)
            end = start.replace(year=start.year + 1) - timedelta(days=1)
            return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")
        if start_date is None or end_date is None:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_DATES_REQUIRED)
        start_date, end_date = str(start_date), str(end_date)
        if not re.fullmatch(r"[0-9]{8}", start_date) or not re.fullmatch(r"[0-9]{8}", end_date):
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_INVALID_DATE)
        try:
            start = datetime.strptime(start_date, "%Y%m%d")
            end = datetime.strptime(end_date, "%Y%m%d")
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_INVALID_DATE) from error
        if start > end:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_INVALID_RANGE)
        return start_date, end_date

    def festival(self, start_date=None, end_date=None):
        # 지역 코드를 보내지 않으므로 전국 검색 결과를 페이지 끝까지 반환한다.
        start_date, end_date = self.validate_festival_dates(start_date, end_date)
        try:
            return [item for _, items in iter_pages(
                self, "searchFestival2",
                {"eventStartDate": start_date, "eventEndDate": end_date},
            ) for item in items]
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE) from error
