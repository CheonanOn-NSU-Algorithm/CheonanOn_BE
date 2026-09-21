# 충남 관광 정보를 API에서 가져오는 코드

import re
from datetime import datetime

import requests

from app.config import Config
from app.errors import BusinessException, ErrorCode

# 충남 코드만 넣어서 시·군·구 구분 없이 전체 조회
CHUNGNAM_REGION_CODE = 44


def with_district(item):
    # 주소에서 지역명 꺼내기. 주소가 안 왔으면 기존 값은 그대로 둠
    result = dict(item)
    if "addr1" not in item:
        return result

    # 예: "충청남도 천안시 동남구 ..." → "천안시 동남구"
    address = item["addr1"]
    match = re.match(
        r"^(?:충청남도|충남)\s+([^\s]+[시군])(?:\s+([^\s]+구)(?=\s|$))?(?=\s|$)",
        address.strip() if isinstance(address, str) else "",
    )
    result["district"] = (
        " ".join(part for part in match.groups() if part) if match else None
    )
    return result


def iter_pages(api, endpoint, params):
    # 한 번에 100건씩, 마지막 페이지까지 가져오기
    page, received, expected = 1, 0, None
    seen = set()
    # 전체 건수가 바뀌거나 같은 페이지가 계속 오면 중단
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
    # 여기서는 API 조회만 하고, DB 저장은 TourSyncService에서 처리

    def __init__(self):
        # 키가 없으면 요청 보내기 전에 에러
        if not Config.TOURAPI_KEY:
            raise BusinessException(ErrorCode.TOUR_API_KEY_MISSING)
        # 키가 이중으로 인코딩되지 않게 먼저 디코딩
        self.api_key = requests.utils.unquote(Config.TOURAPI_KEY)
        self.api_base_url = ("https://apis.data.go.kr/B551011/KorService2")

        # 파라미터 기본값 세팅
        self.default_params = {
            "serviceKey": self.api_key,
            "MobileOS": "ETC",
            "MobileApp": "MyTourApp",
            "_type": "json",
        }

    # 공통으로 API 요청하는 함수
    def request(self, field, params=None):
        # 요청 실패는 BusinessException으로 넘기기
        api_url = f"{self.api_base_url}/{field}"

        # 기본 파라미터 복사
        request_params = self.default_params.copy()

        # 추가 파라미터가 있으면 합치기
        if params:
            request_params.update(params)
        try:
            response = requests.get(
                api_url,
                params=request_params,
                timeout=10
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

        if not isinstance(data, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        api_response = data.get("response")
        if not isinstance(api_response, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        header = api_response.get("header")
        if not isinstance(header, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        # 200 응답이어도 실제 조회는 실패했을 수 있어서 결과 코드도 확인
        result_code = str(header.get("resultCode", ""))
        if result_code != "0000":
            raise BusinessException(ErrorCode.TOUR_API_RESULT_ERROR)

        return data

    # API 응답에서 필요한 item 데이터만 가져오기
    def get_items(self, data):
        if not isinstance(data, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        api_response = data.get("response")
        if not isinstance(api_response, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        body = api_response.get("body")
        if not isinstance(body, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        items = body.get("items", {})
        if not items:
            return []

        if not isinstance(items, dict):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        item_list = items.get("item", [])
        if not isinstance(item_list, list):
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE)

        return item_list

    def _region_items(self, endpoint, params):
        # 전체 페이지를 모아서 각 항목에 지역명 붙이기
        try:
            return [
                with_district(item)
                for _, items in iter_pages(
                    self,
                    endpoint,
                    {
                        **params,
                        "lDongRegnCd": CHUNGNAM_REGION_CODE,
                        "arrange": "A",
                    },
                )
                for item in items
            ]
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_API_INVALID_RESPONSE) from error

    # 콘텐츠 타입별 충청남도 전체 관광 정보 조회
    def get_contents_by_type(self, content_type_id):
        if content_type_id not in {12, 14}:
            raise BusinessException(ErrorCode.TOUR_INVALID_CONTENT_TYPE)
        return self._region_items("areaBasedList2", {"contentTypeId": content_type_id})

    # 충청남도 전체 관광지 조회
    def spots(self):
        """
        관광지 기본정보 조회

        들어있는 정보:
            addr1          주소
            addr2          상세주소
            areacode       지역코드
            contentid      관광지 콘텐츠 ID
            contenttypeid  관광지 콘텐츠 타입 ID
            createdtime    등록일
            firstimage     대표 이미지
            firstimage2    대표 이미지 2
            mapx           경도
            mapy           위도
            modifiedtime   수정일
            tel            전화번호
            title          관광지명
            district       충남 시·군·구 이름(예: 아산시, 천안시 동남구)
        """
        return self.get_contents_by_type(12)

    # 충청남도 전체 문화시설 조회
    def cultural_facilities(self):
        # 문화시설(contentTypeId=14) 기본정보 조회
        return self.get_contents_by_type(14)

    # 콘텐츠 ID 한 건의 공통 상세 정보 조회
    def spots_report(self, spot_id):
        """
        관광지 설명 및 기본 상세정보 조회

        들어있는 정보:
            contentid      관광지 콘텐츠 ID
            contenttypeid  관광지 콘텐츠 타입 ID
            homepage       홈페이지
            overview       관광지 설명
            tel            전화번호
            title          관광지명
            addr1          주소
            addr2          상세주소
            firstimage     대표 이미지
            firstimage2    대표 이미지 2
            mapx           경도
            mapy           위도
        """
        data = self.request(
            "detailCommon2",
            {
                "contentId": spot_id,
                "numOfRows": 10,
                "pageNo": 1,
            }
        )
        return self.get_items(data)

    # 관광지 이용정보 가져오는 기능
    def spots_intro(self, spot_id, content_type_id=12):
        """
        관광지 이용정보 조회

        들어있는 정보:
            infocenter       문의 및 안내 전화번호
            opendate         개장일
            restdate         쉬는 날
            expguide         체험 안내
            expagerange      체험 가능 연령
            accomcount       수용 인원
            useseason        이용 시기
            usetime          이용 시간
            parking          주차 여부 및 주차시설
            chkbabycarriage  유모차 대여 여부
            chkpet           반려동물 동반 가능 여부
            chkcreditcard    신용카드 사용 가능 여부
        """
        data = self.request(
            "detailIntro2",
            {
                "contentId": spot_id,
                "contentTypeId": content_type_id,
                "numOfRows": 10,
                "pageNo": 1,
            }
        )
        return self.get_items(data)

    # 관광지 반복 상세정보 가져오는 기능
    def spots_info(self, spot_id, content_type_id=12):
        """
        관광지 반복 상세정보 조회

        들어있는 정보:
            infoname         상세정보 항목명
            infotext         상세정보 내용
        """
        data = self.request(
            "detailInfo2",
            {
                "contentId": spot_id,
                "contentTypeId": content_type_id,
                "numOfRows": 100,
                "pageNo": 1,
            }
        ) 
        return self.get_items(data)

    # 축제 조회 날짜 검사 및 YYYYMMDD 형식으로 변환
    def validate_festival_dates(self, start_date=None, end_date=None):
        if start_date is None and end_date is None:
            current_year = datetime.now().year
            return f"{current_year}0101", f"{current_year}1231"

        if start_date is None or end_date is None:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_DATES_REQUIRED)

        start_date = str(start_date)
        end_date = str(end_date)

        try:
            parsed_start_date = datetime.strptime(start_date, "%Y%m%d")
            parsed_end_date = datetime.strptime(end_date, "%Y%m%d")
        except ValueError as error:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_INVALID_DATE) from error

        if parsed_start_date > parsed_end_date:
            raise BusinessException(ErrorCode.TOUR_FESTIVAL_INVALID_RANGE)

        return start_date, end_date

    # 축제 조회
    def festival(self, start_date=None, end_date=None):
        """
        충청남도 전체 축제 목록 조회

        들어있는 정보:
            addr1          주소
            addr2          상세주소
            contentid      축제 콘텐츠 ID
            contenttypeid  축제 콘텐츠 타입 ID
            eventstartdate 축제 시작일
            eventenddate   축제 종료일
            firstimage     대표 이미지
            firstimage2    대표 이미지 2
            mapx           경도
            mapy           위도
            tel            전화번호
            title          축제명
            district       충남 시·군·구 이름(예: 아산시, 천안시 동남구)
        """
        start_date, end_date = self.validate_festival_dates(start_date, end_date)
        return self._region_items(
            "searchFestival2",
            {"eventStartDate": start_date, "eventEndDate": end_date},
        )
