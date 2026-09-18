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
        all_spots = []

        # 동남구, 서북구 모두 조회
        for district_name, district_code in self.cheonan_districts.items():
            data = self.request(
                "areaBasedList2",
                {
                    "numOfRows": 100,
                    "pageNo": 1,
                    "contentTypeId": 12,
                    "lDongRegnCd": 44,  # 충청남도
                    "lDongSignguCd": district_code,
                    "arrange": "A",
                }
            )
            spots = self.get_items(data)

            # 어느 구에서 가져온 관광지인지 표시 - 이거 나중에 DB에 저장할 때 필요없으면 제거 1순위 
            for spot in spots:
                spot["district"] = district_name

            # 전체 관광지 목록에 추가
            all_spots.extend(spots)

        return all_spots

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

    # 축제 조회
    def festival(self):
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
        all_festivals = []

        # 동남구, 서북구 모두 조회
        for district_name, district_code in self.cheonan_districts.items():

            data = self.request(
                "searchFestival2",
                {
                    "numOfRows": 100,
                    "pageNo": 1,
                    "eventStartDate": 20260101,
                    "eventEndDate": 20261231,
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
