from datetime import datetime

import requests
from app.config import Config
from app.errors import TourAPIException


class TourAPI:
    def __init__(self):
        #api키 불러올 때 키 값이 없으면 에러 발생시키기
        if not Config.TOURAPI_KEY:
            raise TourAPIException("TOURAPI_KEY가 설정되지 않았습니다.")
        # api 키 불러오기
        self.api_key = requests.utils.unquote(Config.TOURAPI_KEY)
        self.api_base_url = ("https://apis.data.go.kr/B551011/KorService2")

        # 천안시 구 코드 - 동남구: 131, 서북구: 133
        # 충남 지역 코드는 44
        self.cheonan_districts = {"동남구": 131,"서북구": 133}

        # 파라미터 기본값 세팅
        self.default_params = {
            "serviceKey": self.api_key,
            "MobileOS": "ETC",
            "MobileApp": "MyTourApp",
            "_type": "json",
        }

    # 공통으로 API 요청하는 함수
    def request(self, field, params=None):
        api_url = f"{self.api_base_url}/{field}"

        # 기본 파라미터 복사
        request_params = self.default_params.copy()

        # 추가 요구하는 파라미터가 있으면 합치기
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
            raise TourAPIException("TourAPI 응답 시간이 초과되었습니다.") from error
        except requests.exceptions.HTTPError as error:
            raise TourAPIException("TourAPI가 요청 처리에 실패했습니다.") from error
        except requests.exceptions.RequestException as error:
            raise TourAPIException("TourAPI에 연결할 수 없습니다.") from error

        try:
            data = response.json()
        except ValueError as error:
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.") from error

        if not isinstance(data, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        api_response = data.get("response")
        if not isinstance(api_response, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        header = api_response.get("header")
        if not isinstance(header, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        result_code = str(header.get("resultCode", ""))
        if result_code != "0000":
            raise TourAPIException("TourAPI 요청 결과가 실패로 반환되었습니다.")

        return data

    # API 응답에서 필요한 item 데이터만 가져오기
    def get_items(self, data):
        if not isinstance(data, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        api_response = data.get("response")
        if not isinstance(api_response, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        body = api_response.get("body")
        if not isinstance(body, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        items = body.get("items", {})
        if not items:
            return []

        if not isinstance(items, dict):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        item_list = items.get("item", [])
        if not isinstance(item_list, list):
            raise TourAPIException("TourAPI에서 올바르지 않은 응답을 받았습니다.")

        return item_list

    # 콘텐츠 타입별 천안 관광 정보 공통 조회
    def get_contents_by_type(self, content_type_id):
        supported_types = {12, 14}
        if content_type_id not in supported_types:
            raise TourAPIException("지원하지 않는 관광 콘텐츠 타입입니다.")

        all_contents = []

        # 동남구, 서북구 모두 조회
        for district_name, district_code in self.cheonan_districts.items():
            data = self.request(
                "areaBasedList2",
                {
                    "numOfRows": 100,
                    "pageNo": 1,
                    "contentTypeId": content_type_id,
                    "lDongRegnCd": 44,  # 충청남도
                    "lDongSignguCd": district_code,
                    "arrange": "A",
                }
            )
            contents = self.get_items(data)

            # 어느 구에서 가져온 콘텐츠인지 표시
            for content in contents:
                content["district"] = district_name

            all_contents.extend(contents)

        return all_contents

    # 천안의 전체 관광지 조회
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
            district       천안시 구 이름(동남구/서북구)
        """
        return self.get_contents_by_type(12)

    # 천안의 전체 문화시설 조회
    def cultural_facilities(self):
        """문화시설(contentTypeId=14) 기본정보 조회"""
        return self.get_contents_by_type(14)

    # 관광지 설명 가져오는 기능 - 하나씩 불러오는거라 일일 트래픽 조심!
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
            raise TourAPIException("축제 조회 시작일과 종료일을 모두 입력해주세요.")

        start_date = str(start_date)
        end_date = str(end_date)

        try:
            parsed_start_date = datetime.strptime(start_date, "%Y%m%d")
            parsed_end_date = datetime.strptime(end_date, "%Y%m%d")
        except ValueError as error:
            raise TourAPIException("축제 조회 날짜는 YYYYMMDD 형식으로 입력해주세요.") from error

        if parsed_start_date > parsed_end_date:
            raise TourAPIException("축제 조회 시작일은 종료일보다 늦을 수 없습니다.")

        return start_date, end_date

    # 축제 조회
    def festival(self, start_date=None, end_date=None):
        """
        천안 전체 축제 목록 조회

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
            district       천안시 구 이름(동남구/서북구)
        """
        start_date, end_date = self.validate_festival_dates(start_date, end_date)
        all_festivals = []

        # 동남구, 서북구 모두 조회
        for district_name, district_code in self.cheonan_districts.items():

            data = self.request(
                "searchFestival2",
                {
                    "numOfRows": 100,
                    "pageNo": 1,
                    "eventStartDate": start_date,
                    "eventEndDate": end_date,
                    "lDongRegnCd": 44,  # 충청남도
                    "lDongSignguCd": district_code,
                    "arrange": "A",
                }
            )
            festivals = self.get_items(data)

            # 어느 구에서 가져온 축제인지 표시
            for festival in festivals:
                festival["district"] = district_name

            # 전체 축제 목록에 추가
            all_festivals.extend(festivals)

        return all_festivals
