from datetime import datetime, timezone  # created_at/updated_at에 넣을 UTC 시각 생성용

from datetime import datetime
from app import db


class Event(db.Model):
    """행사(Event) 정보를 관리하는 SQLAlchemy ORM 모델 클래스"""
    __tablename__ = 'event'  # MySQL에 실제 생성될 테이블명 지정

    # [1. 기본키 및 식별자]
    # BigInteger: 대용량 데이터를 고려한 64비트 정수형 Primary Key
    # autoincrement=True: 신규 레코드 삽입 시 ID가 1씩 자동 증가
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='행사 ID')

    # [2. 기본 행사 정보]
    # nullable=False: NOT NULL 제약조건 (필수 입력 항목)
    title = db.Column(db.String(200), nullable=False, comment='행사명 (최대 200자)')

    # Enum: 정해진 목록 값만 허용하여 데이터 무결성 보장
    category = db.Column(
        db.Enum('FESTIVAL', 'EXHIBITION', 'PERFORMANCE', 'EXPERIENCE', 'SEASONAL'),
        nullable=False,
        comment='카테고리 (축제/전시/공연/체험/계절행사)'
    )
    region = db.Column(
        db.Enum('DONGNAM', 'SEOBUK'),
        nullable=False,
        comment='행정구역 구분 (동남구/서북구)'
    )

    # [3. 일정 및 시간 정보]
    # Date: 날짜 정보만 저장 (YYYY-MM-DD)
    start_date = db.Column(db.Date, nullable=False, comment='행사 시작일')
    end_date = db.Column(db.Date, nullable=False, comment='행사 종료일 (당일 행사는 start_date와 동일')

    # Time: 시간 정보만 저장 (HH:MM:SS), nullable=True로 설정하여 미정 시 NULL 허용
    start_time = db.Column(db.Time, nullable=True, comment='시작 시각')
    end_time = db.Column(db.Time, nullable=True, comment='종료 시각')

    # [4. 위치 및 지도 좌표 정보]
    location = db.Column(db.String(200), nullable=False, comment='장소명 (예: 천안시민체육공원)')
    address = db.Column(db.String(300), nullable=True, comment='상세 도로명/지번 주소')

    # Numeric(10, 7): 전체 10자리 중 소수점 아래 7자리 보장 (위경도 정밀 좌표용 고정소수점 타입)
    latitude = db.Column(db.Numeric(10, 7), nullable=False, comment='위도 (Latitude)')
    longitude = db.Column(db.Numeric(10, 7), nullable=False, comment='경도 (Longitude)')

    # [5. 요금 정보]
    price_type = db.Column(db.Enum('FREE', 'PAID'), nullable=False, comment='무료/유료 여부')
    # Integer: 일반 정수형 (무료 행사인 경우 NULL 저장 가능)
    price_amount = db.Column(db.Integer, nullable=True, comment='입장 요금(원)')

    # [6. 주최 및 상세 안내 정보]
    organizer = db.Column(db.String(200), nullable=True, comment='주최/주관 기관명')
    contact = db.Column(db.String(100), nullable=True, comment='문의처 전화번호')
    homepage_url = db.Column(db.String(500), nullable=True, comment='공식 홈페이지 링크 URL')

    # Text: 길이에 제한이 없는 대용량 텍스트 저장용 타입
    description = db.Column(db.Text, nullable=True, comment='행사 상세 소개 본문')
    image_url = db.Column(db.String(500), nullable=True, comment='대표 이미지/포스터 URL')

    # [7. 시스템 메타 데이터]
    # DateTime: 날짜와 시간을 모두 저장 (YYYY-MM-DD HH:MM:SS)
    # default=datetime.utcnow: 레코드가 처음 생성되는 시점의 UTC 시간을 자동으로 입력
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment='데이터 등록 일시')

    # 레코드 마지막 수정 시각. default는 최초 생성 시 created_at과 동일하게 채워지고,
    # onupdate=lambda: ... 는 이후 이 row가 UPDATE될 때마다 자동으로 현재 UTC 시각으로 갱신하라는 뜻
    updated_at: datetime = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )